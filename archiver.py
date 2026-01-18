import argparse
import bz2
import compression.zstd
import os
import sys
import tarfile
import tempfile
import time

BUFFER_SIZE = 1024 * 1024


def progress_bar(done, total):
    if total == 0:
        return
    percent = min(100, int(done * 100 / total))
    filled = percent // 2
    bar = "#" * filled + "-" * (50 - filled)
    sys.stdout.write(f"\r[{bar}] {percent}%")
    sys.stdout.flush()


def bz2_compress(src, dst, show_progress):
    total = os.path.getsize(src)
    done = 0

    with open(src, "rb") as fin, bz2.open(dst, "wb") as fout:
        while chunk := fin.read(BUFFER_SIZE):
            fout.write(chunk)
            done += len(chunk)
            if show_progress:
                progress_bar(done, total)
    if show_progress:
        print()


def bz2_decompress(src, dst, show_progress):
    total = os.path.getsize(src)
    done = 0

    with bz2.open(src, "rb") as fin, open(dst, "wb") as fout:
        while chunk := fin.read(BUFFER_SIZE):
            fout.write(chunk)
            done += len(chunk)
            if show_progress:
                progress_bar(done, total)
    if show_progress:
        print()


def zstd_compress(src, dst, show_progress):
    total = os.path.getsize(src)
    done = 0

    with open(src, "rb") as fin, compression.zstd.open(dst, "wb") as fout:
        while chunk := fin.read(BUFFER_SIZE):
            fout.write(chunk)
            done += len(chunk)
            if show_progress:
                progress_bar(done, total)
    if show_progress:
        print()


def zstd_decompress(src, dst, show_progress):
    total = os.path.getsize(src)
    done = 0

    with compression.zstd.open(src, "rb") as fin, open(dst, "wb") as fout:
        while chunk := fin.read(BUFFER_SIZE):
            fout.write(chunk)
            done += len(chunk)
            if show_progress:
                progress_bar(done, total)
    if show_progress:
        print()


def make_tar(source):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tar")
    with tarfile.open(tmp.name, "w") as tar:
        tar.add(source, arcname=os.path.basename(source))
    return tmp.name


def extract_tar(tar_path, target="."):
    with tarfile.open(tar_path) as tar:
        tar.extractall(path=target)


def main():
    parser = argparse.ArgumentParser(
        description="Консольный архиватор/распаковщик (bz2 / zstd)"
    )
    parser.add_argument("source", help="Исходный файл или директория / архив")
    parser.add_argument("target", nargs="?", help="Целевой архив")
    parser.add_argument(
        "-x", "--extract", action="store_true", help="Режим распаковки"
    )
    parser.add_argument(
        "-b", "--benchmark", action="store_true", help="Показать время выполнения"
    )
    parser.add_argument(
        "-p", "--progress", action="store_true", help="Показать прогресс"
    )

    args = parser.parse_args()
    start = time.perf_counter()

    if args.extract:
        src = args.source

        if src.endswith(".bz2"):
            out = src[:-4]
            bz2_decompress(src, out, args.progress)

        elif src.endswith(".zst"):
            out = src[:-4]
            zstd_decompress(src, out, args.progress)

        else:
            raise ValueError("Неподдерживаемый формат архива")

        if out.endswith(".tar"):
            extract_tar(out)
            os.remove(out)

    else:
        if not args.target:
            raise ValueError("Не указан целевой архив")

        src = args.source
        temp_tar = None

        if os.path.isdir(src):
            temp_tar = make_tar(src)
            src = temp_tar

        if args.target.endswith(".bz2"):
            bz2_compress(src, args.target, args.progress)

        elif args.target.endswith(".zst"):
            zstd_compress(src, args.target, args.progress)

        else:
            raise ValueError("Поддерживаются только .bz2 и .zst")

        if temp_tar:
            os.remove(temp_tar)

    if args.benchmark:
        elapsed = time.perf_counter() - start
        print(f"Время выполнения: {elapsed:.3f} сек")


if __name__ == "__main__":
    main()