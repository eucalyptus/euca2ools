#!/usr/bin/python -tt

import argparse
## TODO:  remove the stuff above and add the regular license header
import hashlib
import multiprocessing
import itertools
import os.path
import progressbar
import random
import subprocess
import sys
import tarfile
import threading
import time


def _add_fileobj_to_tarball(infile, outfile):
    tarball = tarfile.open(mode='w|', fileobj=outfile)
    try:
        tarinfo = tarfile.TarInfo(os.path.basename(infile.name))
        tarinfo.size = os.path.getsize(infile.name)
        tarball.addfile(tarinfo=tarinfo, fileobj=infile)
    finally:
        tarball.close()


def write_tarball(infile, outfile):
    widgets = ['Bundling ', progressbar.Bar(), ' ', progressbar.Percentage(),
               ' ', progressbar.FileTransferSpeed(), ' ', progressbar.ETA()]
    bar = progressbar.ProgressBar(maxval=os.path.getsize(infile.name),
                                  widgets=widgets)
    tar_thread = threading.Thread(target=_add_fileobj_to_tarball,
                                  args=(infile, outfile))
    tar_thread.start()
    bar.start()
    while tar_thread.is_alive():
        bar.update(infile.tell())
        time.sleep(0.25)
    tar_thread.join()
    bar.finish()


def calc_digest_and_exit(in_fileno, out_fileno, result_pipe):
    infile = os.fdopen(in_fileno)
    outfile = os.fdopen(out_fileno, 'w')
    digest = hashlib.sha1()
    while True:
        chunk = infile.read(65536)
        if chunk:
            digest.update(chunk)
            outfile.write(chunk)
        else:
            break
    result_pipe.send(digest.hexdigest())
    result_pipe.close()
    infile.close()
    outfile.close()
    sys.exit()


def bundle_image(image_filename, bundle_filename):
    # pipe for getting the digest from sha1sum
    digest_pipe_out, digest_pipe_in = multiprocessing.Pipe(duplex=False)
    # pipe for getting the part info from the part writer
    writer_pipe_out, writer_pipe_in = multiprocessing.Pipe(duplex=False)
    # pipe for tar --> sha1sum
    tar_out_pipe_out, tar_out_pipe_in = os.pipe()
    # pipe for sha1sum --> gzip
    sha_out_pipe_out, sha_out_pipe_in = os.pipe()

    # tar --> sha1sum
    # Digest calculation is a little more processor-intensive, so it goes in
    # its own process.
    # That conveniently lets us avoid the annoyances of passing lots of data
    # between two threads by letting us simply use OS pipes.
    pid = os.fork()
    if pid == 0:
        digest_pipe_out.close()
        os.close(tar_out_pipe_in)
        os.close(sha_out_pipe_out)
        calc_digest_and_exit(tar_out_pipe_out, sha_out_pipe_in, digest_pipe_in)
    digest_pipe_in.close()
    os.close(tar_out_pipe_out)
    os.close(sha_out_pipe_in)

    # sha1sum --> gzip
    try:
        gzip = subprocess.Popen(['pigz', '-c'], stdin=sha_out_pipe_out,
                                stdout=subprocess.PIPE, close_fds=True,
                                bufsize=-1)
    except OSError:
        gzip = subprocess.Popen(['gzip', '-c'], stdin=sha_out_pipe_out,
                                stdout=subprocess.PIPE, close_fds=True,
                                bufsize=-1)
    os.close(sha_out_pipe_out)

    # gzip --> openssl
    srand = random.SystemRandom()
    key = format(srand.getrandbits(128), 'x')
    iv = format(srand.getrandbits(128), 'x')
    openssl = subprocess.Popen(['openssl', 'enc', '-e', '-aes-128-cbc',
                                '-K', key, '-iv', iv], stdin=gzip.stdout,
                               stdout=subprocess.PIPE, close_fds=True,
                               bufsize=-1)

    # openssl --> writer
    writer_thread = threading.Thread(target=write_parts,
                                     args=(openssl.stdout, bundle_filename,
                                           writer_pipe_in))
    writer_thread.start()

    # Drive everything by feeding tar
    with open(image_filename) as image:
        with os.fdopen(tar_out_pipe_in, 'w') as tar_input:
            write_tarball(image, tar_input)
        writer_thread.join()

        digest = digest_pipe_out.recv()
        digest_pipe_out.close()
        parts = writer_pipe_out.recv()
        writer_pipe_out.close()
    return (parts, digest, key, iv)


PART_SIZE = 1024 * 1024


def write_parts(infile, part_prefix, result_pipe):
    parts = []
    for part_no in itertools.count():
        part_fname = '{0}.part.{1}'.format(part_prefix, part_no)
        print 'Writing part', part_fname
        part_info = _write_single_part(infile, part_fname)
        parts.append(part_info)
        if part_info['size'] < PART_SIZE:
            # That's the last part
            result_pipe.send(parts)
            return


def _write_single_part(infile, part_fname):
    part_digest = hashlib.sha1()
    with open(part_fname, 'w') as part:
        bytes_to_write = PART_SIZE
        while bytes_to_write > 0:
            chunk = infile.read(min((bytes_to_write, 65536)))
            if chunk:
                part.write(chunk)
                part_digest.update(chunk)
                bytes_to_write -= len(chunk)
            else:
                break
        return {'path': part_fname, 'digest': part_digest.hexdigest(),
                'size': part.tell()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image_filename')
    parser.add_argument('bundle_filename')
    args = parser.parse_args()
    result = bundle_image(args.image_filename, args.bundle_filename)
    print result
