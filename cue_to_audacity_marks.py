import os.path
import sys
import typing


def parse_cue(cuefile) -> tuple[typing.Optional[str], typing.Optional[str], list[dict]]:
    is_last_line = False
    in_tracks_zone = False
    artist_name = None
    album_name = None
    tracks = []
    current_track = None
    indices = []
    linenum = 0
    while not is_last_line:
        curline = cuefile.readline()
        linenum += 1
        if not (curline.endswith("\n") or curline.endswith("\r")):
            is_last_line = True
        curline = curline.rstrip("\r\n").strip()
        params = curline.split(" ", 1)
        directive = params[0]
        params = params[1:]
        if directive == "PERFORMER":
            if artist_name is None:
                artist_name = params[0].strip('"')
        elif directive == "TITLE":
            if not in_tracks_zone:
                album_name = params[0].strip('"')
            else:
                current_track["title"] = params[0].strip('"')
        elif directive == "TRACK":
            in_tracks_zone = True
            params = params[0].split(" ")
            if params[1] != "AUDIO":
                continue  # Ignore non-audio entries just in case
            if current_track:
                current_track["times"] = indices
                tracks.append(current_track)
            current_track = {}
            indices = []
        elif directive == "INDEX":
            if not in_tracks_zone:
                raise RuntimeError(f"Error in file {cuefile.name} at line {linenum}: Unexpected 'INDEX' directive.")
            params = params[0].split(" ")
            if len(indices) > 2:
                raise RuntimeError(f"Error in file {cuefile.name} at line {linenum}: Only 2 indices are supported.")
            indices.append(params[1])
    if current_track:
        current_track["times"] = indices
        tracks.append(current_track)
    return album_name, artist_name, tracks


def timemark_to_seconds(time_mark: str) -> float:
    minutes, seconds, frames = time_mark.split(":")
    result = int(minutes) * 60 + int(seconds) + (round(float(frames) / 75, 6))
    return result


def write_track_audacity_marks(track_fmt: str, tracks: list[dict], outfile: typing.TextIO):
    for track in tracks:
        track_time_mark = track["times"][-1]
        track_start_time = timemark_to_seconds(track_time_mark)
        outfile.write(f"{track_start_time:.6f}\t{track_start_time:.6f}\t{track_fmt.format(track_name=track['title'])}\n")


def transform(path: str):
    with open(path, "r", encoding="utf-8") as cuefile:
        album_name, artist_name, tracks = parse_cue(cuefile)
    if not tracks:
        return
    with open(f"{os.path.splitext(path)[0]}_audmark.txt", "w") as outfile:
        fmt = "{track_name}"
        if album_name is not None:
            fmt = f"{album_name} - {fmt}"
        if artist_name is not None:
            fmt = f"{artist_name} - {fmt}"
        write_track_audacity_marks(fmt, tracks, outfile)


def main():
    for filename in sys.argv[1:]:
        transform(filename)
    return 0


if __name__ == "__main__":
    sys.exit(main())
