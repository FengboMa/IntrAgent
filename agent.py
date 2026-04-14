import openai
import json
import datetime
import re
import os

from prompts import main_prompt, get_detail_prompt, evaluation_prompt_confidence_level_1, evaluation_prompt_confidence_level_2, evaluation_prompt_confidence_level_3, full_set_answer_prompt
from examples import aio_example
from main_prompt_instructions import aio_main_prompt_instructions, main_prompt_instructions_confidence_level_1, main_prompt_instructions_confidence_level_2, main_prompt_instructions_confidence_level_3

class LLMChunkProcessor:
    def __init__(self, config_path="config.json", question=None, knowledge_chunks=None):
        """
        Initializes the LLM agent by loading configuration from a JSON file.
        """
        self.config = self.load_config(config_path)
        api_key = self.config.get("openai_api_key", "")
        base_url = self.config.get("base_url",None)
        self.max_tokens = self.config.get("max_tokens", 1000)
        self.temperature = self.config.get("temperature", 0)
        self.model = self.config.get("model", "gpt-4o")
        
        if base_url:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = openai.OpenAI(api_key=api_key)
        
        self.soft_cap = self.config.get("soft_cap", 3)
        self.confidence_level = self.config.get("confidence_level", 2)
        
        self.question = question if question is not None else ""
        self.knowledge_chunks = knowledge_chunks if knowledge_chunks is not None else []
    
        self.observation_stage_chunk = ""
        self.observation_stage_get_detail = ""
        self.observation_stage_evaluation = ""
        self.observation_stage_evaluation_full_set = ""
        self.sufficiency = ""
        
        self.past_action = ""
        self.past_sufficiency = []
        
        self.log = ""
        self.current_chunk_index = 0
        self.current_step_index = 0

    @staticmethod
    def load_config(config_path):
        """
        Loads configuration settings from a JSON file.
        """
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
                print(f"Configuration loaded from file: {config_path}")
            return config
        except Exception as e:
            raise RuntimeError(f"Error loading config file: {str(e)}")
            
    def _call_LLM(self, prompt):
        """
        Calls OpenAI GPT-4o API using the new OpenAI v1.0.0+ client.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a scientific research assistant that always gives thorough, in-depth, and well-organized answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        # ---- token usage straight from OpenAI ------------------------
        usage = response.usage                # an object in openai‑python ≥1.0
        print(
            f"prompt_tokens={usage.prompt_tokens}, "
            f"completion_tokens={usage.completion_tokens}, "
            f"total={usage.total_tokens}"
        )

        # (Optional) rough cost estimate
        price_per_1k_prompt = 0.005  # <-- plug in current model pricing
        price_per_1k_comp   = 0.020
        cost = (usage.prompt_tokens/1_000)*price_per_1k_prompt + (usage.completion_tokens/1_000)*price_per_1k_comp
        print(f"Approx cost ${cost:.4f}")
        return response.choices[0].message.content.strip()
    
    def parse_response(self, response):
        """
        Parses the LLM response to extract reasoning steps and action.
        """
        reasoning_match = re.search(r"Reasoning Steps:\s*(.+?)\n", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(\w+)", response)

        reasoning_steps = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided."
        action = action_match.group(1).strip().upper() if action_match else "UNKNOWN ACTION"

        return reasoning_steps, action

    def get_chunk(self):
        """
        Retrieves the next chunk from self.knowledge_chunks and updates the observation stage.
        """
        
        if self.current_chunk_index < min(self.soft_cap, len(self.knowledge_chunks)-1):
            # Retrieve the current chunk and increment the index
            chunk = self.knowledge_chunks[self.current_chunk_index]
            chunk_number = self.current_chunk_index + 1
            self.current_chunk_index += 1
            
            chunk_entry = f"""
            Here is an additional chunk, this is chunk {chunk_number} out of {len(self.knowledge_chunks)-1} chunks:
            Chunk {chunk_number}:
            
            {chunk}
            """
            print(f"Step {self.current_step_index}: GET_CHUNK \n")
            self.past_action += f"Step {self.current_step_index}: GET_CHUNK \n"
            
            self.observation_stage_chunk = chunk_entry
            
            print(f"Chunk Entry: {chunk_entry}")
            
            self.log += f"\n ========== \n Step {self.current_step_index}: GET_CHUNK \n"
            self.log += chunk_entry
            self.log += f"\n====\n "
            
            self.current_step_index += 1
            return chunk
        else:
            return None

    def get_detail_chunk(self):
        """
        Summarizes the current chunk and updates the observation stage.
        """
        prompt =get_detail_prompt.format(question=self.question, chunk=self.observation_stage_chunk)
        
        response = self._call_LLM(prompt)
        
        reasoning_match = re.search(r"Reasoning Steps:\s*(.+?)\n", response, re.DOTALL)
        get_detail_match = re.search(r"Details:\s*(.+)", response, re.DOTALL)

        get_detail_reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided."
        get_detail = get_detail_match.group(1).strip() if get_detail_match else "No get_detail provided."

        get_detail_entry = f"""
        ----------------------------------------------------
        [Chunk {self.current_chunk_index} Details]
        
        This is chunk {self.current_chunk_index} out of {len(self.knowledge_chunks)-1} chunks.
        ----------------
        {get_detail}
        ----------------------------------------------------
        """
        print(f"Get_detail Entry: {get_detail_entry}")

        self.past_action += f"Step {self.current_step_index}: GET_DETAIL \n"
        
        self.observation_stage_get_detail = get_detail_entry
        
        self.log += f"\n ========== \n Step {self.current_step_index}: GET_DETAIL \n"
        self.log += prompt
        self.log += f"\n====\n "
        self.log += response
        
        self.current_step_index += 1

        return get_detail_reasoning, get_detail
        

    def evaluate(self):
        """
        Evaluates the observation stage and determines if the question can be answered.
        """
        
        if self.confidence_level == 1:
            prompt = evaluation_prompt_confidence_level_1.format(question=self.question, observation_stage=self.observation_stage_get_detail)
        elif self.confidence_level == 2:
            prompt = evaluation_prompt_confidence_level_2.format(question=self.question, observation_stage=self.observation_stage_get_detail)
        elif self.confidence_level == 3:
            prompt = evaluation_prompt_confidence_level_3.format(question=self.question, observation_stage=self.observation_stage_get_detail)
        else:
            raise ValueError("Invalid confidence level. Choose between 1, 2, or 3.")

        response = self._call_LLM(prompt)

        sufficiency_match = re.search(r"Sufficiency:\s*(YES|NO|PARTIAL)", response)
        explanation_match = re.search(r"Explanation:\s*(.+)", response, re.DOTALL)
        get_detail_answer_match = re.search(r"Detail_Answer:\s*(.+)", response, re.DOTALL)

        sufficiency = sufficiency_match.group(1).strip() if sufficiency_match else "NO SUFFICIENCY PROVIDED."
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        get_detail_answer = get_detail_answer_match.group(1).strip() if get_detail_answer_match else "NO SUM_ANS PROVIDED."
        
        print(f"Sufficiency: {sufficiency}")
        print(f"Detail_Answer: {get_detail_answer}")
        
        evaluation_entry = f"""
        ----------------------------------------------------
        [Chunk {self.current_chunk_index} Evaluation]
        
        This is chunk {self.current_chunk_index} out of {len(self.knowledge_chunks)-1} chunks.
        ----------------
        Sufficiency of the chunk: {sufficiency}
        
        The answer provided by reading the details: {get_detail_answer}
        ----------------------------------------------------
        """
        print(f"Evaluation Entry: {evaluation_entry}")
        self.past_sufficiency.append(sufficiency)
        self.past_action += f"Step {self.current_step_index}: EVALUATE \n"
        print(self.past_sufficiency)
        self.observation_stage_evaluation = evaluation_entry
        self.observation_stage_evaluation_full_set += evaluation_entry
        
        self.log += f"\n ========== \n Step {self.current_step_index}: EVALUATE \n"
        self.log += prompt
        self.log += f"\n====\n "
        self.log += response
        
        self.current_step_index += 1
        return sufficiency, explanation, get_detail_answer
    
    def full_set_answer(self):
        """
        After processing all chunks or when sufficient information is gathered,
        generates a final answer based on all evaluation entries.
        """
        prompt = full_set_answer_prompt.format(
            question=self.question, 
            observation_stage=self.observation_stage_evaluation_full_set
        )

        response = self._call_LLM(prompt)

        final_answer = response
        print(f"Final Answer: {final_answer}")

        evaluation_entry = f"""
        ----------------------------------------------------
        [Final Answer Evaluation]
        
        Final Answer:
        {final_answer}
        ----------------------------------------------------
        """
        print(f"Final Answer Evaluation Entry: {evaluation_entry}")

        self.past_action += f"Step {self.current_step_index}: FINAL ANSWER \n"
        self.log += f"\n ========== \n Step {self.current_step_index}: FINAL ANSWER \n"
        self.log += prompt
        self.log += f"\n====\n "
        self.log += response
        self.current_step_index += 1

        return final_answer

    def terminate(self):
        """
        Ends the process, synthesizes a final answer from the evaluations,
        logs the final answer, and returns it.
        """
        self.past_action += f"Step {self.current_step_index}: TERMINATE \n"
        self.log += f"\n ========== \n Step {self.current_step_index}: TERMINATE \n"
        
        final_answer = self.full_set_answer()

        self.final_answer = final_answer
        self.log += f"\nFinal Answer: {final_answer}\n"

        self.current_step_index += 1

        return final_answer

    def answer_question(self, question=None, knowledge_chunks=None):
        """
        Processes knowledge chunks sequentially to answer a given question.
        """
        if question is not None:
            self.question = question
        if knowledge_chunks is not None:
            self.knowledge_chunks = knowledge_chunks

        answer = None
        
        print("Starting question answering process...")
        print(f"Total knowledge chunks: {len(self.knowledge_chunks)-1}")
        print("\n" + "=" * 60)
        print(f"Execution Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Model Used: {self.model}")
        print(f"Max Tokens: {self.max_tokens}")
        print(f"Temperature: {self.temperature}")
        print(f"Confidence Level: {self.confidence_level}")
        print(f"Soft Cap: {self.soft_cap}")
        print("-" * 40 + "\n")

        # Iterate while there are more chunks and within the soft cap
        max_steps = self.soft_cap
        steps = 0
        while self.current_chunk_index < min(self.soft_cap, len(self.knowledge_chunks)):
            if steps >= max_steps:
                print(f"soft_cap/max_steps {max_steps} reached, breaking loop.")
                break
            print("====================")
            print(f"This is iteration for chunk index {self.current_chunk_index}.")
            answer = None
            last_action = self.past_action.strip().split("\n")[-1].strip() if self.past_action.strip() else ""
            if "EVALUATE" in last_action:
                past_sufficiency_str = "\n".join(
                    [f"    Chunk {i + 1}: {val}" for i, val in enumerate(self.past_sufficiency)]
                )
                evaluation_section = (
                    f"\n---\nEvaluation Result of the last evaluation step if the details gathered is enough:\n"
                    f"    {self.sufficiency}\n"
                    f"Past sufficiency evaluated:\n{past_sufficiency_str}\n"
                )
            else:
                evaluation_section = ""
            if self.confidence_level == 1:
                main_prompt_instructions = main_prompt_instructions_confidence_level_1
            elif self.confidence_level == 2:
                main_prompt_instructions = main_prompt_instructions_confidence_level_2
            elif self.confidence_level == 3:
                main_prompt_instructions = main_prompt_instructions_confidence_level_3
            else:
                raise ValueError("Invalid confidence level. Choose between 1, 2, or 3.")
            prompt = main_prompt.format(
                main_prompt_instructions=main_prompt_instructions,
                examples = aio_example,
                past_action=self.past_action, 
                current_chunk_index=self.current_chunk_index+1,
                total_chunks_len=len(self.knowledge_chunks),
                evaluation_result=evaluation_section
            )
            print(f"Prompt: {prompt}\n")
            output_text = self._call_LLM(prompt)
            reasoning_steps, action = self.parse_response(output_text)
            self.log += f"\n  xxxxxxxxxxxxxxxxxxxxxxxxxx\n Step {self.current_step_index}: LLM output log \n"
            self.log += prompt
            self.log += f"\n  xxxxxxxxx"
            self.log += output_text
            self.log += f"\n  xxxxxxxxxxxxxxxxxxxxxxxxxx"
            if action == "GET_CHUNK":
                chunk = self.get_chunk()
                if chunk is None:
                    print("🔹 No more knowledge chunks available.")
                    answer = self.full_set_answer()
                    self.answer = answer
                    self.log += f"\nFinal Answer: {answer}\n"
                    break
            elif action == "GET_DETAIL":
                self.get_detail_chunk()
            elif action == "EVALUATE":
                self.evaluate()
            elif action == "TERMINATE":
                answer = self.terminate()
                break
            else:
                print(f"Warning: Unrecognized action '{action}'.")
            steps += 1
        # After loop, always call full_set_answer if answer is None
        if answer is None:
            note = f"[DEBUG]  soft_cap/max_steps reached ({max_steps}) or all chunks processed. answer is None.\n"
            answer = self.full_set_answer()
            answer = note + answer
        
        print("\n**Final Answer:**\n" + "=" * 60)
        print(answer)
        print("=" * 60 + "\n")

        return answer
