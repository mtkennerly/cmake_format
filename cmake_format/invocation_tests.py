from __future__ import unicode_literals
import difflib
import io
import os
import shutil
import subprocess
import sys
import unittest
import tempfile


class TestInvocations(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    super(TestInvocations, self).__init__(*args, **kwargs)
    self.tempdir = None
    self.tempconfig = None

  def setUp(self):
    self.tempdir = tempfile.mkdtemp(prefix='cmakeformattest_')
    thisdir = os.path.realpath(os.path.dirname(__file__))

    self.env = {
        'PYTHONPATH': os.path.dirname(thisdir)
    }

    configpath = os.path.join(thisdir, 'test/cmake-format.py')
    self.tempconfig = os.path.join(self.tempdir, '.cmake-format.py')
    shutil.copyfile(configpath, self.tempconfig)

  def tearDown(self):
    shutil.rmtree(self.tempdir)

  def test_pipeout_invocation(self):
    """
    Test invocation with an infile path and output to stdout.
    """

    thisdir = os.path.realpath(os.path.dirname(__file__))
    infile_path = os.path.join(thisdir, 'test', 'test_in.cmake')
    expectfile_path = os.path.join(thisdir, 'test', 'test_out.cmake')

    with io.open(os.path.join(self.tempdir, 'test_out.cmake'), 'wb') as outfile:
      subprocess.check_call([sys.executable, '-Bm', 'cmake_format',
                             infile_path], stdout=outfile, cwd=self.tempdir,
                            env=self.env)

    with io.open(os.path.join(self.tempdir, 'test_out.cmake'), 'r',
                 encoding='utf8') as infile:
      actual_text = infile.read()
    with io.open(expectfile_path, 'r', encoding='utf8') as infile:
      expected_text = infile.read()

    delta_lines = list(difflib.unified_diff(expected_text.split('\n'),
                                            actual_text.split('\n')))
    if delta_lines:
      raise AssertionError('\n'.join(delta_lines[2:]))

  def test_fileout_invocation(self):
    """
    Test invocation with an infile path and outfile path
    """

    thisdir = os.path.realpath(os.path.dirname(__file__))
    infile_path = os.path.join(thisdir, 'test', 'test_in.cmake')
    expectfile_path = os.path.join(thisdir, 'test', 'test_out.cmake')

    subprocess.check_call([sys.executable, '-Bm', 'cmake_format',
                           '-o', os.path.join(self.tempdir, 'test_out.cmake'),
                           infile_path], cwd=self.tempdir, env=self.env)

    with io.open(os.path.join(self.tempdir, 'test_out.cmake'), 'r',
                 encoding='utf8') as infile:
      actual_text = infile.read()
    with io.open(expectfile_path, 'r', encoding='utf8') as infile:
      expected_text = infile.read()

    delta_lines = list(difflib.unified_diff(expected_text.split('\n'),
                                            actual_text.split('\n')))
    if delta_lines:
      raise AssertionError('\n'.join(delta_lines[2:]))

  def test_inplace_invocation(self):
    """
    Test invocation for inplace format of a file
    """

    thisdir = os.path.realpath(os.path.dirname(__file__))
    infile_path = os.path.join(thisdir, 'test', 'test_in.cmake')
    expectfile_path = os.path.join(thisdir, 'test', 'test_out.cmake')

    ofd, tmpfile_path = tempfile.mkstemp(suffix='.txt', prefix='CMakeLists',
                                         dir=self.tempdir)
    os.close(ofd)
    shutil.copyfile(infile_path, tmpfile_path)
    subprocess.check_call([sys.executable, '-Bm', 'cmake_format',
                           '-i', tmpfile_path], cwd=self.tempdir, env=self.env)

    with io.open(os.path.join(tmpfile_path), 'r', encoding='utf8') as infile:
      actual_text = infile.read()
    with io.open(expectfile_path, 'r', encoding='utf8') as infile:
      expected_text = infile.read()

    delta_lines = list(difflib.unified_diff(expected_text.split('\n'),
                                            actual_text.split('\n')))
    if delta_lines:
      raise AssertionError('\n'.join(delta_lines[2:]))

  def test_stream_invocation(self):
    """
    Test invocation with stdin as the infile and stdout as the outifle
    """

    thisdir = os.path.realpath(os.path.dirname(__file__))
    infile_path = os.path.join(thisdir, 'test', 'test_in.cmake')
    expectfile_path = os.path.join(thisdir, 'test', 'test_out.cmake')

    stdinpipe = os.pipe()
    stdoutpipe = os.pipe()

    def preexec():
      os.close(stdinpipe[1])
      os.close(stdoutpipe[0])

    # pylint: disable=W1509
    proc = subprocess.Popen([sys.executable, '-Bm', 'cmake_format', '-'],
                            stdin=stdinpipe[0], stdout=stdoutpipe[1],
                            cwd=self.tempdir, env=self.env, preexec_fn=preexec)
    os.close(stdinpipe[0])
    os.close(stdoutpipe[1])

    with io.open(infile_path, 'r', encoding='utf-8') as infile:
      with io.open(stdinpipe[1], 'w', encoding='utf-8') as outfile:
        for line in infile:
          outfile.write(line)

    with io.open(stdoutpipe[0], 'r', encoding='utf-8') as infile:
      actual_text = infile.read()

    proc.wait()

    with io.open(expectfile_path, 'r', encoding='utf8') as infile:
      expected_text = infile.read()

    delta_lines = list(difflib.unified_diff(expected_text.split('\n'),
                                            actual_text.split('\n')))
    if delta_lines:
      raise AssertionError('\n'.join(delta_lines[2:]))

  def test_encoding_invocation(self):
    """
    Try to reformat latin1-encoded file, once with default
    encoding (-> prompt utf8-decoding error) and once with
    specifically latin1 encoding (-> should succeed)
    """

    thisdir = os.path.realpath(os.path.dirname(__file__))
    infile_path = os.path.join(thisdir, 'test', 'test_latin1_in.cmake')
    expectfile_path = os.path.join(thisdir, 'test', 'test_latin1_out.cmake')

    # this invocation should fail
    invocation_result = subprocess.call(
        [sys.executable, '-Bm', 'cmake_format',
         '--outfile-path', os.path.join(self.tempdir, 'test_latin1_out.cmake'),
         infile_path],
        cwd=self.tempdir, env=self.env,
        stderr=subprocess.PIPE)
    self.assertNotEqual(
        0, invocation_result,
        msg="Expected cmake-format invocation to fail but did not")

    # this invocation should succeed
    subprocess.check_call(
        [sys.executable, '-Bm', 'cmake_format',
         '--input-encoding=latin1',
         '--output-encoding=latin1',
         '--outfile-path', os.path.join(self.tempdir, 'test_latin1_out.cmake'),
         infile_path],
        cwd=self.tempdir, env=self.env)

    with io.open(os.path.join(self.tempdir, 'test_latin1_out.cmake'), 'r',
                 encoding='latin1') as infile:
      actual_text = infile.read()

    with io.open(expectfile_path, 'r', encoding='latin1') as infile:
      expected_text = infile.read()

    delta_lines = list(difflib.unified_diff(expected_text.split('\n'),
                                            actual_text.split('\n')))
    if delta_lines:
      raise AssertionError('\n'.join(delta_lines[2:]))

  def test_no_config_invocation(self):
    """
    Test invocation with no config file specified
    """
    os.unlink(self.tempconfig)
    thisdir = os.path.realpath(os.path.dirname(__file__))
    infile_path = os.path.join(thisdir, 'test', 'test_in.cmake')
    expectfile_path = os.path.join(thisdir, 'test', 'test_out.cmake')

    subprocess.check_call([sys.executable, '-Bm', 'cmake_format',
                           '-o', os.path.join(self.tempdir, 'test_out.cmake'),
                           infile_path], cwd=self.tempdir, env=self.env)

    with io.open(os.path.join(self.tempdir, 'test_out.cmake'), 'r',
                 encoding='utf8') as infile:
      actual_text = infile.read()
    with io.open(expectfile_path, 'r', encoding='utf8') as infile:
      expected_text = infile.read()

    delta_lines = list(difflib.unified_diff(expected_text.split('\n'),
                                            actual_text.split('\n')))
    if delta_lines:
      raise AssertionError('\n'.join(delta_lines[2:]))


if __name__ == '__main__':
  unittest.main()
