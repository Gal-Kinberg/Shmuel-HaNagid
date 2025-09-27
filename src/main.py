# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from docx import Document
from pathlib import Path
import os
import pyparsing as pp
from pyparsing.unicode import pyparsing_unicode as ppu
import re
import difflib
from apparatus_classes import *
import pandas as pd

def has_hebrew_letters(text):
    return bool(re.search(r'[א-ת]', text))


nums = pp.nums
alphasnums = ppu.Hebrew.alphas + nums + "'?!\":,;.ֵַּׄׄ"

# Define the grammar for a Hebrew word
hebrew_word = pp.Word(alphasnums)
bold_word = pp.Suppress('*') + hebrew_word + pp.Suppress('*')
hebrew_sentence = pp.OneOrMore(hebrew_word | "..." | "[!]").setResultsName("regular")
italic_sentence = '_' + hebrew_sentence.setResultsName("italic") + '_'
strike_sentence = '~' + hebrew_sentence.setResultsName("strike") + '~'

complex_sentence = pp.OneOrMore(italic_sentence | strike_sentence | hebrew_sentence)
pp_variant_apparatus = pp.Group(complex_sentence).setResultsName("text") + pp.Group(pp.OneOrMore(bold_word)).setResultsName("sources")
pp_lemma_apparatus = pp.Group(hebrew_sentence).setResultsName("lemma") + pp.Suppress(']') + pp.OneOrMore(pp.Group(pp_variant_apparatus)).setResultsName("variants")
pp_line_apparatus = pp.Word(nums).setResultsName("line") + pp.delimitedList(pp.Group(pp_lemma_apparatus), delim=pp.Suppress('/')).setResultsName("lemmata")
pp_title_apparatus = pp.delimitedList(pp.Group(pp_lemma_apparatus), delim=pp.Suppress('/')).setResultsName("lemmata")
pp_full_apparatus = pp_title_apparatus.setResultsName("title_apparatus") + pp.OneOrMore(pp.Group(pp_line_apparatus)).setResultsName("lines")


def extract_ranges(text):
    # 1. Extract the whole group after the phrase
    match = re.search(
        r'(?:נוסח הפנים לבתים|נוסח הפנים לכתובת ולבתים)\s*'
        r'(\d+(?:-\d+)?(?:\s*,\s*\d+(?:-\d+)?)*)',
        text
    )
    if not match:
        return []

    # 2. Split by commas into individual ranges
    parts = [p.strip() for p in match.group(1).split(',')]

    # 3. Expand ranges into full list of numbers
    numbers = []
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            numbers.extend(range(start, end + 1))
        else:
            numbers.append(int(part))

    return numbers

def extract_comment(parsed_text):
    if "italic" in parsed_text:
        comment = ' '.join(parsed_text['italic'])
    else:
        comment = None
    return comment
def extract_comment_raw(text):
    if "_" in text:
        comment = ''.join([character for character in text[text.index('_')+1:] if character not in "_~*"]).strip()
    else:
        comment = None
    return comment

def contains_but_not_other(text):
    return bool(re.search(r'נוסח הפנים(?! לכתובת)', text)) or 'נוסח הפנים לכתובת ולשיר' in text

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    folder_path = r"C:\Users\Gankl\PycharmProjects\ShmuelHaNagid\data\first_run"  # Replace with the actual path to your folder

    correction_list = []

    for entry_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, entry_name)
        if os.path.isfile(full_path):
            print(f"File found: {full_path}")
            # Perform operations on the file here
            filepath = full_path
            # filepath = r"C:\Users\Gankl\PycharmProjects\ShmuelHaNagid\data\אלוה עז.docx"
            # filepath = r"C:\Users\Gankl\PycharmProjects\ShmuelHaNagid\data\תנומה בעין מכיר.docx"

            path_objecth = Path(filepath)
            filename = path_objecth.stem

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

            # Parse the test string
            for paragraph in joined_paragraphs[-1::-1]:
                print(paragraph)
                if "מקורות:" == paragraph.split()[0]:
                    print("found sources")
                    break

            # sources_split = re.split(r'\*[^\s]*\*', paragraph)
            sources_split = paragraph.split(r'*')
            sources_details = [(source, details) for source, details in zip(sources_split[1::2], sources_split[2::2])]
            source_to_line_dict = {}
            for source, details in sources_details:
                line_numbers = extract_ranges(details)  # list of integers
                if line_numbers:
                    source_to_line_dict[source] = line_numbers
                elif contains_but_not_other(details):
                    source_to_line_dict[source] = list(range(1, 501))  # assume all lines are of this source


            line_to_source_dict = {line: source for source in source_to_line_dict for line in
                                   source_to_line_dict[source]}

            # Parse the test string
            parsed = None
            for paragraph in joined_paragraphs[-1::-1]:
                print(paragraph)
                try:
                    parsed = pp_full_apparatus.parseString(paragraph)
                    print("Parsing succeeded.")
                    break
                except Exception as e:
                    print(f"Failed to parse the text. Error: {e}")

            if not parsed:
                print("Did not find any apparatus. Skipping file.")
                continue

            # Print the parsed result
            variant_list = []
            for line_apparatus in parsed['lines']:
                line = line_apparatus['line']
                for lemma_apparatus in line_apparatus['lemmata']:
                    try:
                        lemma = lemma_apparatus['lemma']
                        lemma_source = line_to_source_dict[int(line)]

                        # find if the lemma is from a different source
                        for variant in lemma_apparatus['variants']:
                            if "נוסח הפנים לפי" in ' '.join(variant['text']) or "הושלם לפי" in ' '.join(variant['text']):
                                lemma_source = "ש" if "ש" in variant['sources'] else variant['sources'][0]

                        for variant in lemma_apparatus['variants']:
                            variant_text = variant['text']
                            manuscripts = variant['sources']
                            print(
                                f"Line: {line}  |  Correction from: {' '.join(lemma)}, to: {' '.join(variant_text)}, in manuscripts: {manuscripts}")
                            for manuscript in manuscripts:
                                variant_list.append({
                                    'line': line,
                                    'lemma': ' '.join(lemma),
                                    'text': ' '.join(variant_text),
                                    'target': manuscript,
                                    'source': lemma_source
                                })
                    except Exception as e:
                        print(f"Error: {e}")

            for test in variant_list:
                try:
                    match = re.search(r'_.*\bחסר\b.*_', test['text'])
                    if match:
                        correction = MissingApparatus(
                            song_name=filename,
                            line=int(test['line']),
                            lemma=test['lemma'],
                            source=test['source'],
                            target=test['target']
                        )
                    elif "~" in test['text']:
                        # parsed_strike_through = re.search(r'~(.*?)~', test)
                        # parsed_strike_through_text = parsed_strike_through.group(1).strip()
                        parsed_strike_through = complex_sentence.parseString(test['text'])
                        deleted = ' '.join(parsed_strike_through['strike'])
                        corrected = ' '.join(parsed_strike_through['regular']) if 'regular' in parsed_strike_through else ''

                        comment = extract_comment_raw(test['text'])
                        if deleted != corrected:
                            correction = DeletionApparatus(deleted=deleted,
                                                           corrected=corrected,
                                                           song_name=filename,
                                                           line=int(test['line']),
                                                           lemma=test['lemma'],
                                                           source=test['source'],
                                                           target=test['target'],
                                                           comment=comment)
                    else:
                        comment = extract_comment_raw(test['text'])
                        parsed_text = complex_sentence.parseString(test['text'])
                        if 'regular' not in parsed_text:
                            # just a comment without correction
                            # comment = extract_comment(parsed_text)
                            correction = Apparatus(
                                song_name=filename,
                                line=int(test['line']),
                                lemma=test['lemma'],
                                source=test['source'],
                                target=test['target'],
                                comment=comment
                            )

                        else:
                            # check if same number of words
                            correction_text = ' '.join(parsed_text['regular'])

                            # print(f"before strip: {correction_text}")
                            correction_text = correction_text.strip("!?,:\'\"[](); ")
                            # print(f"after strip: {correction_text}")

                            if len(test['lemma'].split()) != len(correction_text.split()):
                                # comment = extract_comment(parsed_text)
                                correction = WordSwapApparatus(
                                    text=' '.join(parsed_text['regular']),
                                    song_name=filename,
                                    line=int(test['line']),
                                    lemma=test['lemma'],
                                    source=test['source'],
                                    target=test['target'],
                                    comment=comment
                                )
                            else:
                                ## compare letters
                                # check if first or last letters are אהוי, and if so remove them for the comparison
                                lemma_to_compare = test['lemma']
                                correction_to_compare = correction_text

                                if correction_to_compare[0] in 'אהוי':
                                    correction_to_compare = correction_to_compare[1:]
                                if len(correction_to_compare) > 0 and correction_to_compare[-1] in 'אהוי':
                                    correction_to_compare = correction_to_compare[:-1]
                                if lemma_to_compare[0] in 'אהוי':
                                    lemma_to_compare = lemma_to_compare[1:]
                                if len(lemma_to_compare) > 0 and lemma_to_compare[-1] in 'אהוי':
                                    lemma_to_compare = lemma_to_compare[:-1]

                                char_diff = list(difflib.ndiff(lemma_to_compare, correction_to_compare))

                                added_chars = [char[2:] for char in char_diff if char.startswith('+ ')]
                                removed_chars = [char[2:] for char in char_diff if char.startswith('- ')]

                                only_ahevi = True
                                for char in set(added_chars + removed_chars):
                                    if char not in 'אהוי':
                                        only_ahevi = False
                                        break

                                only_added_or_removed = ((len(removed_chars) > 0 and len(added_chars) == 0) or (
                                            len(removed_chars) == 0 and len(added_chars) > 0))
                                if only_ahevi and only_added_or_removed:
                                    # comment = extract_comment(parsed_text)
                                    correction = FullSpellingApparatus(
                                        text=correction_text,
                                        song_name=filename,
                                        line=int(test['line']),
                                        lemma=test['lemma'],
                                        source=test['source'],
                                        target=test['target'],
                                        comment=comment
                                    )
                                else:
                                    # check word lengths
                                    same_lengths = True
                                    for i in range(len(correction_text.split())):
                                        if len(correction_text.split()[i]) != len(test['lemma'].split()[i]):
                                            same_lengths = False
                                            break

                                    if not same_lengths:
                                        # comment = extract_comment(parsed_text)
                                        correction = WordSwapApparatus(
                                            text=correction_text,
                                            song_name=filename,
                                            line=int(test['line']),
                                            lemma=test['lemma'],
                                            source=test['source'],
                                            target=test['target'],
                                            comment=comment
                                        )

                                    else:
                                        # diff characters again, now with full text
                                        char_diff = list(difflib.ndiff(test['lemma'], correction_text))
                                        added_chars = [char[2:] for char in char_diff if char.startswith('+ ')]
                                        removed_chars = [char[2:] for char in char_diff if char.startswith('- ')]

                                        if not added_chars and not removed_chars:
                                            # if nothing was added or removed, skip it
                                            continue

                                        removal_index = test['lemma'].index(removed_chars[0])
                                        insertion_index = correction_text.index(added_chars[0])

                                        # check if only word order changed
                                        if set(test['lemma'].split()) == set(correction_text.split()):
                                            # comment = extract_comment(parsed_text)
                                            correction = OrderSwapApparatus(
                                                text=correction_text,
                                                song_name=filename,
                                                line=int(test['line']),
                                                lemma=test['lemma'],
                                                source=test['source'],
                                                target=test['target'],
                                                comment=comment
                                            )
                                        # check if only one letter changed, at the same place
                                        elif len(added_chars) == 1 and len(
                                                removed_chars) == 1 and removal_index == insertion_index:
                                            # letter swap
                                            # comment = extract_comment(parsed_text)
                                            correction = LetterSwapApparatus(
                                                text=correction_text,
                                                old_letter=removed_chars[0],
                                                new_letter=added_chars[0],
                                                song_name=filename,
                                                line=int(test['line']),
                                                lemma=test['lemma'],
                                                source=test['source'],
                                                target=test['target'],
                                                comment=comment
                                            )
                                        else:
                                            # general word swap
                                            # comment = extract_comment(parsed_text)
                                            correction = WordSwapApparatus(
                                                text=correction_text,
                                                song_name=filename,
                                                line=int(test['line']),
                                                lemma=test['lemma'],
                                                source=test['source'],
                                                target=test['target'],
                                                comment=comment
                                            )

                    # print(correction)
                    correction_list.append(correction)
                except Exception as e:
                    print(f"EXCEPTION: Error occurred while parsing: {e}")
                    continue

            # for correction in correction_list:
            #     print(correction.to_json())
            # for appratype in set([_.type for _ in correction_list]):
            #     print(
            #         f"Number of {appratype}: {len([_ for _ in correction_list if _.type == appratype])} | Percentage of {appratype}: {len([_ for _ in correction_list if _.type == appratype]) / len(correction_list) * 100:.2f}%")

    # import re
    #
    # pattern = r'^(?P<number>\d+)?(?:\t)?(?P<text1>[א-ת\s\W/]+?)(?:(?:\t+)(?P<text2>[א-ת\s\W\d/]+))?$'
    #
    #
    # def parse_line(line):
    #     match = re.match(pattern, line)
    #     if match:
    #         parts = match.groupdict()
    #         # Clean up None values and strip whitespace
    #         return {k: v.strip() if v else None for k, v in parts.items()}
    #     return None


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
