aio_main_prompt_instructions = """
1. You should only take actions based on the current knowledge provided.
2. You should issue only one action at a time.
3. Knowledge chunks are ordered by relevance, meaning earlier chunks may contain the most useful information regarding the question.
4. If your Past Action Taken is GET_CHUNK, you have to use SUMMARIZE_CHUNK action to summarize it with respect to the research question, rather than do it yourself.
5. If your Past Action Taken is SUMMARIZE_CHUNK, you have to use EVALUATE action to determine if summary gathered so far would answer the question correctly or not, rather than do it yourself.
6. Terminate the process once you have enough information to provide a conclusive answer.
7. Pay attention to number of chunk you are working with. If the past action was evaluating on the last chunk available. TERMINATE the process if running out of knowledge chunks.
8. After reasoning step by step, output Action only
"""

main_prompt_instructions_confidence_level_1 = """
1. You will be provided with a list of knowledge chunks, ordered by relevance to the research question. Earlier chunks are more likely to contain useful information.
2. Your task is to iteratively retrieve a knowledge chunk, extract relevant details, and evaluate whether you can answer the research question. Repeat this process until you have evaluated all available knowledge chunks or gathered enough information to confidently terminate.
3. You will be given a list of predefined actions to select from.
4. In each iteration, you must select exactly one action based on the current observation.
5. The observation includes: the current chunk index, the total number of available chunks, and the list of past actions taken.
6. The available actions are: GET_CHUNK, GET_DETAIL, EVALUATE, and TERMINATE, as defined in the action list.
7. If the most recent action in the past actions taken was GET_CHUNK, your next action **must** be GET_DETAIL to extract information from the current knowledge chunk — do not perform this extraction yourself.
8. If the most recent action was GET_DETAIL, your next action **must** be EVALUATE to assess whether the gathered details are sufficient to answer the research question — do not perform the evaluation yourself.
9. You must select only one action at a time — never choose multiple actions in a single step.
10. Since knowledge chunks are ordered by relevance to the research question, earlier chunks are more likely to contain useful information. Use this ordering to guide your reading sequence.
11. You must TERMINATE the process only after either (a) all available knowledge chunks have been evaluated, or (b) you are confident that the research question can be answered based on the most recent evaluation.
12. Pay attention to the total number of knowledge chunks. If your most recent EVALUATE action was performed on the **last available chunk**, you must TERMINATE the process regardless of the outcome.
13. The expected workflow is: GET_CHUNK → GET_DETAIL → EVALUATE → TERMINATE (if evaluation result is sufficient). If not, continue to the next chunk. If you reach the final chunk and the evaluation is still insufficient, you must TERMINATE.
14. Do not TERMINATE early based solely on assumptions about relevance. Always continue until a conclusive evaluation result is available or all chunks are exhausted.
15. After your reasoning, output your response in the specified format.
"""
# 11,13,14 are different from the 2.

main_prompt_instructions_confidence_level_2 = """
1. You will be provided with a list of knowledge chunks, ordered by relevance to the research question. Earlier chunks are more likely to contain useful information.
2. Your task is to iteratively retrieve a knowledge chunk, extract relevant details, and evaluate whether you can answer the research question. Repeat this process until you can confidently terminate.
3. You will be given a list of predefined actions to select from.
4. In each iteration, you must select exactly one action based on the current observation.
5. The observation includes: the current chunk index, the total number of available chunks, and the list of past actions taken.
6. The available actions are: GET_CHUNK, GET_DETAIL, EVALUATE, and TERMINATE, as defined in the action list.
7. If the most recent action in the past actions taken was GET_CHUNK, your next action **must** be GET_DETAIL to extract information from the current knowledge chunk — do not perform this extraction yourself.
8. If the most recent action was GET_DETAIL, your next action **must** be EVALUATE to assess whether the gathered details are sufficient to answer the research question — do not perform the evaluation yourself.
9. You must select only one action at a time — never choose multiple actions in a single step.
10. Since knowledge chunks are ordered by relevance to the research question, earlier chunks are more likely to contain useful information. Use this ordering to guide your reading sequence.
11. You must TERMINATE the process once you have gathered enough information to confidently answer the research question.
12. Pay attention to the total number of knowledge chunks. If your most recent EVALUATE action was performed on the **last available chunk** and the result was insufficient, you must TERMINATE the process due to lack of additional information.
13. The expected workflow is: GET_CHUNK → GET_DETAIL → EVALUATE → TERMINATE (if evaluation result is sufficient). If not, continue to the next chunk. If you reach the final chunk and the evaluation is still insufficient, you must TERMINATE.
14. You may TERMINATE early if an EVALUATE action confirms that the gathered information is sufficient to answer the research question with high confidence.
15. After your reasoning, output your response in the specified format.
"""

main_prompt_instructions_confidence_level_3 = """
1. You will be provided with a list of knowledge chunks, ordered by relevance to the research question. Earlier chunks are more likely to contain useful information.
2. Your task is to iteratively retrieve a knowledge chunk, extract relevant details, and evaluate whether you can answer the research question. Repeat this process until you can confidently terminate.
3. You will be given a list of predefined actions to select from.
4. In each iteration, you must select exactly one action based on the current observation.
5. The observation includes: the current chunk index, the total number of available chunks, and the list of past actions taken.
6. The available actions are: GET_CHUNK, GET_DETAIL, EVALUATE, and TERMINATE, as defined in the action list.
7. If the most recent action in the past actions taken was GET_CHUNK, your next action **must** be GET_DETAIL to extract information from the current knowledge chunk — do not perform this extraction yourself.
8. If the most recent action was GET_DETAIL, your next action **must** be EVALUATE to assess whether the gathered details are sufficient to answer the research question — do not perform the evaluation yourself.
9. You must select only one action at a time — never choose multiple actions in a single step.
10. Since knowledge chunks are ordered by relevance to the research question, earlier chunks are more likely to contain useful information. Use this ordering to guide your reading sequence.
11. You may TERMINATE the process as soon as you believe that additional knowledge chunks are unlikely to provide significantly better information, even if you are not fully confident.
12. If your most recent EVALUATE action was performed on the **last available chunk**, you must TERMINATE the process regardless of the outcome.
13. The expected workflow is: GET_CHUNK → GET_DETAIL → EVALUATE → TERMINATE. You may also TERMINATE early based on the assumption that remaining chunks have diminishing relevance.
14. Terminate aggressively if your evaluation suggests NO from continuing, even if high confidence has not yet been achieved.
15. After your reasoning, output your response in the specified format.
"""

# 11,13,14 are different from the 2.