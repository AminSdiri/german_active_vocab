import pysrt

def fetch_subs_from_timestamp(srt_object: pysrt.srtitem.SubRipItem, minute: int, second: int) -> tuple[str, list]:
    '''progressivly expand time window until a subtitle is found'''
    for time_window in range(1, 60):
        subtitle_slice = srt_object.slice(starts_before={'minutes': minute,
                                                    'seconds': second+2*time_window},
                                        ends_after={'minutes': minute,
                                                    'seconds': second-2*time_window})
        if subtitle_slice:
            break
        if time_window == 60:
            # TODO (4) reconvert minutes to hours:minutes
            raise Exception(f'No German Subtitles found between {minute-2}:{second} and {minute+2}:{second}')

    # weirdly it give the index of the next subtitle_phrase
    index_list = [subtitle_phrase.index -1 for subtitle_phrase in subtitle_slice]

    slice_text = ''.join([f' – {subtitle_phrase.text}' for subtitle_phrase in subtitle_slice])
    return slice_text, index_list

def get_phrase_text(srt_object: pysrt.srtitem.SubRipItem, slice_indexes: list, jump_to: str, mode: str) -> tuple[str, list]:
    if jump_to=='next' and mode=='replace':
        slice_indexes = [max(slice_indexes)+1]
    elif jump_to=='previous' and mode=='replace':
        slice_indexes = [min(slice_indexes)-1]
    elif jump_to=='next' and mode=='append':
        slice_indexes.append(max(slice_indexes)+1)
    elif jump_to=='previous' and mode=='append':
        slice_indexes.insert(0, min(slice_indexes)-1)
    else:
        raise RuntimeError('jump_to should be "previous" or "next", mode should be "replace" or "append"')

    slice_text = ''.join([f' – {srt_object[x].text}' for x in slice_indexes])

    return slice_text, slice_indexes

def format_example(video_title: str, example: str) -> str:
    # updated
    example = example.replace("'", "//QUOTE").replace('"', "//DOUBLEQUOTE")
    example += f' ({video_title})'
    example = example.strip()
    return example

def clean_subtitle(subs: str) -> str:
    subs = subs.replace('</i>', '')\
               .replace('<i>', '')\
               .replace('– –', '–')\
               .replace('-', '–')\
               .replace('– –', '–')\
               .replace("\n", " ")
    return subs
