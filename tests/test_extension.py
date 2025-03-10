#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def test_install_extension(lib):
    lib.cmd('extension install hello')
    lib.cmd('hello')


def test_install_extension_with_github_syntax(lib):
    lib.cmd('extension install clk-project/hello')
    lib.cmd('hello')


def test_update_extension(lib):
    lib.cmd('extension install hello')
    lib.cmd('extension update hello')
    lib.cmd('hello --update-extension')


def test_copy_extension(lib):
    lib.cmd('extension create someext')
    lib.cmd('parameter --global-someext set echo test')
    assert lib.cmd('echo') == 'test'
    lib.cmd('extension disable someext')
    assert lib.cmd('echo') == ''
    lib.cmd('extension copy someext someext2')
    assert lib.cmd('echo') == 'test'
    lib.cmd('extension disable someext2')
    assert lib.cmd('echo') == ''


def test_move_extension(lib):
    lib.cmd('extension create someext')
    lib.cmd('parameter --global-someext set echo test')
    assert lib.cmd('echo') == 'test'
    lib.cmd('extension disable someext')
    assert lib.cmd('echo') == ''
    lib.cmd('extension rename someext someext2')
    assert lib.cmd('echo') == 'test'
    lib.cmd('extension disable someext2')
    assert lib.cmd('echo') == ''
    lib.cmd('extension enable someext')
    assert lib.cmd('echo') == ''
