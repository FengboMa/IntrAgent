import os
import re
import ast
import json
import openai

from rank_prompts import tree_structure_prompt, ranking_prompt

class MarkdownPaperProcessor:
    def __init__(self, md_dir: str, question: str, config_path="config.json"):
        """
        Initializes the processor with a markdown directory, research question, 
        and configuration loaded from a JSON file.
        """
        self.md_dir = md_dir
        self.question = question
        self.config = self.load_config(config_path)
        api_key = self.config.get("openai_api_key", "")
        base_url = self.config.get("base_url",None)
        self.soft_cap = self.config.get("soft_cap", 3)
        self.max_tokens = self.config.get("max_tokens", 1000)
        self.temperature = self.config.get("temperature", 0)
        self.model = self.config.get("model", "gpt-4o")
        if base_url:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = openai.OpenAI(api_key=api_key)
        
    @staticmethod
    def load_config(config_path):
        """
        Loads configuration settings from a JSON file.
        """
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
            return config
        except Exception as e:
            raise RuntimeError(f"Error loading config file: {str(e)}")

    def _call_LLM(self, prompt: str):
        """
        Calls the OpenAI using the configured parameters.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful science research assistant that is knowledgeable about the physics field. You will be asked to read academic papers and answer questions based on the information you read."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        usage = response.usage       
        print(
            f"prompt_tokens={usage.prompt_tokens}, "
            f"completion_tokens={usage.completion_tokens}, "
            f"total={usage.total_tokens}"
        )

        return response.choices[0].message.content.strip()

    def parse_markdown(self, filepath: str):
        """
        Parses a markdown file and returns a list of tuples: (index, heading, text).
        """
        headings = {}
        with open(filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()
        current_heading = None
        content = []
        for line in lines:
            match = re.match(r"^(#+)\s*(.*)", line)
            if match:
                if current_heading:
                    headings[current_heading] = "\n".join(content).strip()
                    content = []
                current_heading = match.group(2).strip()
            elif current_heading:
                content.append(line.strip())
        if current_heading:
            headings[current_heading] = "\n".join(content).strip()
        return [(idx + 1, heading, text) for idx, (heading, text) in enumerate(headings.items())]

    def update_headings(self, parsed_markdown, new_headings):
        """
        Updates the parsed markdown headings with the new headings provided.
        """
        if len(parsed_markdown) != len(new_headings):
            raise ValueError("New heading list length must match the original")
        return [
            (idx + 1, new_heading, content)
            for (idx, (_, _, content)), new_heading in zip(enumerate(parsed_markdown), new_headings)
        ]

    def get_tree_structure(self, headings: list):
        # Format the prompt by replacing the {headings} placeholder
        prompt = tree_structure_prompt.format(headings=headings)
        response_text = self._call_LLM(prompt)
        output_text = response_text.replace("```python", "").replace("```", "").strip()
        try:
            structured_list = ast.literal_eval(output_text)
        except Exception as e:
            print(f"Error parsing tree structure output: {e}")
            print(f"Raw output: {output_text}")
            structured_list = None
        return structured_list

    def get_ranking(self, main_title_heading: str, formatted_headings: list):
        # Format the ranking prompt by replacing the placeholders
        prompt = ranking_prompt.format(
            main_title_heading=main_title_heading,
            question=self.question,
            formatted_headings="\n".join(formatted_headings)
        )
        ranking_response = self._call_LLM(prompt)
        return ranking_response

    def extract_ranking(self, response: str):
        """
        Extracts the ranking string from the LLM response.
        """
        final_ranking_match = re.search(r"\*\*Final ranking:\*\*\s*(.+)", response)
        if final_ranking_match:
            ranking_raw = final_ranking_match.group(1)
            numbers = re.findall(r"<<<(.*?)>>>", ranking_raw)
            ranking_output = ",".join(numbers)
            # print("Extracted Ranking:", ranking_output)
            return ranking_output
        else:
            print("Final ranking not found in response.")
            return None

    def process_file(self, file_path: str):
        """
        Processes a single markdown file:
        1. Parses the markdown.
        2. Generates a tree structure from the headings.
        3. Updates headings, filters empty entries, and drops the main title.
        4. Formats section titles.
        5. Calls the LLM to rank sections and reorders them accordingly.
        Returns a dictionary with the file name, main title, final entries, and formatted headings.
        """
        indexed_headings = self.parse_markdown(file_path)
        headings = [heading for _, heading, _ in indexed_headings]
        print(f"Processing file: {os.path.basename(file_path)}")
        print("Indexed Headings:")
        print(headings)
        
        structured_list = self.get_tree_structure(headings)
        if structured_list and isinstance(structured_list, list) and len(structured_list) == len(headings):
            updated_indexed_headings = self.update_headings(indexed_headings, structured_list)
        else:
            print("Unexpected tree structure output or length mismatch. Using original headings.")
            updated_indexed_headings = indexed_headings
        
        # Remove empty entries
        filtered_entries = [
            (new_index + 1, heading, text)
            for new_index, (old_index, heading, text) in enumerate(updated_indexed_headings)
            if text.strip()
        ]
        
        # Drop the first entry and store its heading as the main title
        if filtered_entries:
            _, main_title_heading, _ = filtered_entries[0]
            filtered_entries = filtered_entries[1:]
        else:
            main_title_heading = ""
        
        # Prepend section title to content
        prepended_entries = [
            (new_idx, heading, f"Section_title: {heading}\n{text}")
            for new_idx, (_, heading, text) in enumerate(filtered_entries, 1)
        ]

        # Reindex remaining entries
        reindexed_entries = [
            (new_index + 1, heading, text)
            for new_index, (_, heading, text) in enumerate(prepended_entries)
        ]

        
        # Format headings for display
        formatted_headings = [
            f'<<<{index}>>>: {heading}'
            for index, heading, _ in reindexed_entries
        ]
        section_title_list = '; '.join(formatted_headings)
        print("Formatted Section Titles:")
        print(section_title_list)
        
        # Get ranking from LLM
        ranking_response = self.get_ranking(main_title_heading, formatted_headings)
        print("Ranking Response:")
        print(ranking_response)
        
        ranking_output = self.extract_ranking(ranking_response)
        if ranking_output:
            print("Extracted Ranking:", ranking_output)
            ranking_indices = [int(x.strip()) for x in ranking_output.split(",")]
            entry_dict = {index: (index, heading, text) for index, heading, text in reindexed_entries}
            reordered_entries = [entry_dict[i] for i in ranking_indices if i in entry_dict]
        else:
            print("No valid ranking output; using original order.")
            reordered_entries = reindexed_entries
        
        return {
            "file": os.path.basename(file_path),
            "main_title": main_title_heading,
            "entries": reordered_entries,
            "formatted_entries": section_title_list
        }

    def process_all_files(self):
        """
        Processes all markdown files in the given directory.
        Returns a dictionary mapping file names to their processed results.
        """
        results = {}
        for file in os.listdir(self.md_dir):
            if file.endswith(".md"):
                file_path = os.path.join(self.md_dir, file)
                result = self.process_file(file_path)
                results[file] = result
        return results

if __name__ == "__main__":
    md_directory = r"C:\path\to\your\markdown_files"
    question = "Your research question goes here."
    config_path = "config.json"

    processor = MarkdownPaperProcessor(md_directory, question, config_path)
    results = processor.process_all_files()