# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from docx import Document
import re

def has_hebrew_letters(text):
    return bool(re.search(r'[א-ת]', text))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    filepath = r"C:\Users\Gankl\PycharmProjects\ShmuelHaNagid\data\אלוה עז.docx"
    # filepath = r"C:\Users\Gankl\PycharmProjects\ShmuelHaNagid\data\תנומה בעין מכיר.docx"
    doc = Document(filepath)
    paragraph_list = []
    for para in doc.paragraphs:
        if para.runs:
            runs = []
            curr_run = ''
            # Initialize the first run's attributes
            curr_bold = para.runs[0].bold
            curr_italic = para.runs[0]._element.rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}iCs') is not None if (para.runs[0]._element.rPr is not None) else False
            curr_strike = para.runs[0].font.strike if para.runs[0].font else False
            for irun, run in enumerate(para.runs):
                element = run._element.rPr if run._element.rPr is not None else None
                if element is not None:
                    has_i = element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}i') is not None
                    has_iCs = element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}iCs') is not None
                    # print(f"italics: {has_i}  |  italicsCs: {has_iCs}")
                else:
                    has_i = False
                    has_iCs = False

                # print(f'Run Number: {irun}\t|\tRun: {run.text}\t|\tBold: {run.bold}\t|\tItalics: {has_iCs}')
                if (run.bold != curr_bold or has_iCs != curr_italic or run.font.strike != curr_strike) and run.text.strip():
                    if curr_run:
                        runs.append({"text": curr_run, "bold": curr_bold, "italics": curr_italic, "strike": curr_strike})
                    curr_run = run.text
                    curr_bold = run.bold
                    curr_italic = has_iCs
                    curr_strike = run.font.strike if run.font else False
                else:
                    curr_run += run.text

            runs.append({"text": curr_run, "bold": curr_bold, "italics": curr_italic, "strike": curr_strike})
            # if runs:
            paragraph_list.append(runs)

        # else:
            # # If there are no runs, just append the plain text
            # paragraph_list.append([])

    # Join the runs in each paragraph into a single string, adding formatting inline
    joined_paragraphs = []
    for para in paragraph_list:
        joined_text = ''
        for run in para:
            left_spaces = len(run['text']) - len(run['text'].lstrip())
            run['text'] = run['text'].lstrip()
            right_spaces = len(run['text']) - len(run['text'].rstrip())
            run['text'] = run['text'].rstrip()  # Strip whitespace from the text
            if run['text'] == '':
                run['bold'] = False  # If text is empty, set bold to False
                run['italics'] = False
                run['strike'] = False

            run['text'] = run['text'].split() if run['bold'] else [run['text']]  # Split text if bold

            # format the text based on its attributes
            formatted_text = ''
            for text in run['text']:
                if run['bold'] and has_hebrew_letters(text):
                    formatted_text += f"*{text}* "  # for bold text, there could be multiple words, so we add a space after each word
                elif run['italics'] and has_hebrew_letters(text):
                    formatted_text += f"_{text}_"
                elif run['strike'] and has_hebrew_letters(text):
                    formatted_text += f"~{text}~"
                else:
                    formatted_text += f"{text}"
            joined_text += ' ' * left_spaces + f"{formatted_text.strip()}" + ' ' * right_spaces
        joined_paragraphs.append(joined_text.strip())

    import re

    pattern = r'^(?P<number>\d+)?(?:\t)?(?P<text1>[א-ת\s\W/]+?)(?:(?:\t+)(?P<text2>[א-ת\s\W\d/]+))?$'


    def parse_line(line):
        match = re.match(pattern, line)
        if match:
            parts = match.groupdict()
            # Clean up None values and strip whitespace
            return {k: v.strip() if v else None for k, v in parts.items()}
        return None


    # # Example usage
    # test_strings = [
    #     "1\tשלום עולם",
    #     "23\tבית כנסת/תפילה\t\t\tמקום קדוש 123",
    #     "\tשיר השירים\tשלמה המלך",
    # ]
    #
    # for string in [paragraph_list[7][0]['text']]:
    #     result = parse_line(string)
    #     print(f"Input: {string}")
    #     print(f"Parsed: {result}\n")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
