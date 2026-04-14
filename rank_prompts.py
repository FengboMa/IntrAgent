tree_structure_prompt = """
You are an expert in scientific research and academic writing, proficient in analyzing the structural organization of research papers. Your task is to infer the hierarchical structure of a research paper based on a list of section titles provided in sequential order.

---

### **Task**
You are given a list of section titles extracted from a research paper, shown in the order they appear in the document:

{headings}

These titles are not annotated to indicate their level (e.g., section, subsection, sub-subsection). Your job is to infer the **tree structure** by determining which titles are:
- **Main sections**
- **Subsections** under a main section
- **Sub-subsections** under a subsection

---

### **Rules**
- Maintain the **original order** of the titles.
- Do **not** introduce any new titles or remove existing ones.
- Use the **first title** as the likely **main title** of the paper, unless it's clearly a preamble (e.g., "Abstract", "Introduction").
- Infer nesting levels based on typical academic paper structure and semantic cues in the titles.
- Structure the output using this format:
  - `"Section Title"` (main section)
  - `"Section Title - Subsection Title"` (subsection)
  - `"Section Title - Subsection Title - Sub-subsection Title"` (sub-subsection)

---

### **Example**

Given:

["Experiment setup", "sample preparation", "device setup", "SERS measurements", "Result and Discussion"]

Expected output:

["Experiment setup", 
 "Experiment setup - sample preparation", 
 "Experiment setup - device setup", 
 "Experiment setup - SERS measurements", 
 "Result and Discussion"]

---

### **Expected Output Format**
- Provide the inferred tree structure in a Python list format.
- Follow the form: `["Section", "Section - Subsection", "Section - Subsection - Sub-subsection", ...]`
- Output **only the list**. Do not include explanations, reasoning steps, or extra comments.

---

Let's think step by step.
"""

ranking_prompt = """
You are an AI research assistant with expertise in analyzing academic papers. Your task is to determine which sections of a paper are most likely to contain the answer to a given research question. The section titles are provided in a **tree structure**, where main sections and their subsections are denoted using a hyphen ("-"). Your goal is to rank these sections and subsections from **most relevant to least relevant** in relation to the research question.

---

**Paper Title**: {main_title_heading}

**Research Question**: {question}

**Section Titles**:
{formatted_headings}

---

### **Instructions**
- Analyze the research question and the structure of the section titles.
- Rank the section titles in order of likelihood to contain the answer — from most to least relevant.
- Subsections may be more specific than main sections; use their nesting to guide your ranking.
- For each section in the ranking, provide a **one-sentence explanation** for its placement.
- Maintain the original order of section titles when relevance is tied.
- Do **not** skip or omit any section titles from the list.
- Format the final ranking using only integer indices, enclosed in <<<#>>> brackets, based on the position of each title in the provided list (starting from 1).
- Do not repeat section titles or include any extra commentary after the final ranking.

---

### **Response Template**

Reasoning steps:

1. [Title 1] — [1-sentence justification]
2. [Title 2] — [1-sentence justification]
...

**Final ranking:** <<<2>>>, <<<1>>>, <<<3>>>, ... <<<n>>>

Let's think step by step.
"""
