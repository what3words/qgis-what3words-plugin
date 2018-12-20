# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import zipfile
import json
from collections import defaultdict

from paver.easy import *


options(
    plugin = Bunch(
        name = 'what3words',
        source_dir = path('what3words'),
        ext_libs = path('what3words/extlibs'),
        ext_src = path('what3words/ext-src'),
        package_dir = path('.'),
        tests = ['tests'],
        excludes = [
            '*.pyc',
            '.git',
            '*.pro',
            'ext-src',
        ],
        # skip certain files inadvertently found by exclude pattern globbing
        skip_exclude = []
    ),

    sphinx = Bunch(
        docroot = path('docs'),
        sourcedir = path('docs/source'),
        builddir = path('docs/build')
    )
)


@task
def setup(options):
    """Install run-time dependencies"""
    clean = getattr(options, 'clean', False)
    ext_libs = options.plugin.ext_libs
    ext_src = options.plugin.ext_src
    if clean:
        ext_libs.rmtree()
    ext_libs.makedirs()

    runtime, test = read_requirements()
    os.environ['PYTHONPATH']=ext_libs.abspath()
    for req in runtime + test:
        sh('pip3 install -U -t %(ext_libs)s %(dep)s' % {
            'ext_libs' : ext_libs.abspath(),
            'dep' : req
        })

@task
def install(options):
    '''install plugin to qgis'''
    builddocs(options)
    plugin_name = options.plugin.name
    src = path(__file__).dirname() / plugin_name
    if os.name == 'nt':
        dst = path('~/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins').expanduser() / plugin_name
    elif sys.platform == 'darwin':
        dst = path(' ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins').expanduser() / plugin_name
    else:
        dst = path('~/.local/share/QGIS/QGIS3/profiles/default/python/plugins').expanduser() / plugin_name
    print("Destination folder for plugin: " + str(dst))
    src = src.abspath()
    dst = dst.abspath()
    if os.name == 'nt':
        dst.rmtree()
        src.copytree(dst)
    elif not dst.exists():
        src.symlink(dst)
        # Symlink the build folder to the parent
        docs = path('..') / '..' / "docs" / 'build' / 'html'
        docs_dest = path(__file__).dirname() / plugin_name / "docs"
        docs_link = docs_dest / 'html'
        if not docs_dest.exists():
            docs_dest.mkdir()
        if not docs_link.islink():
            docs.symlink(docs_link)

def read_requirements():
    """Return a list of runtime and list of test requirements"""
    lines = path('requirements.txt').lines()
    lines = [ l for l in [ l.strip() for l in lines] if l ]
    divider = '# test requirements'

    try:
        idx = lines.index(divider)
    except ValueError:
        raise BuildFailure(
            'Expected to find "%s" in requirements.txt' % divider)

    not_comments = lambda s,e: [ l for l in lines[s:e] if l[0] != '#']
    return not_comments(0, idx), not_comments(idx+1, None)

@task
@cmdopts([
    ('tests', 't', 'Package tests with plugin'),
])
def package(options):
    """Create plugin package
    """
    builddocs(options)
    package_file = options.plugin.package_dir / ('%s.zip' % options.plugin.name)
    with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        if not hasattr(options.package, 'tests'):
            options.plugin.excludes.extend(options.plugin.tests)
        _make_zip(zf, options)
    return package_file

def _make_zip(zipFile, options):
    excludes = set(options.plugin.excludes)
    skips = options.plugin.skip_exclude

    src_dir = options.plugin.source_dir
    exclude = lambda p: any([path(p).fnmatch(e) for e in excludes])
    def filter_excludes(root, items):
        if not items:
            return []
        # to prevent descending into dirs, modify the list in place
        for item in list(items):  # copy list or iteration values change
            itempath = path(os.path.relpath(root)) / item
            if exclude(item) and item not in skips:
                debug('Excluding %s' % itempath)
                items.remove(item)
        return items

    for root, dirs, files in os.walk(src_dir):
        for f in filter_excludes(root, files):
            relpath = os.path.relpath(root)
            zipFile.write(path(root) / f, path(relpath) / f)
        filter_excludes(root, dirs)

    for root, dirs, files in os.walk(options.sphinx.builddir):
        for f in files:
            relpath = os.path.join(options.plugin.name, "docs", os.path.relpath(root, options.sphinx.builddir))
            zipFile.write(path(root) / f, path(relpath) / f)


def create_settings_docs(options):
    settings_file = path(options.plugin.name) / "settings.json"
    doc_file = options.sphinx.sourcedir / "settingsconf.rst"
    try:
        with open(settings_file) as f:
            settings = json.load(f)
    except:
        return
    grouped = defaultdict(list)
    for setting in settings:
        grouped[setting["group"]].append(setting)
    with open (doc_file, "w") as f:
        f.write(".. _plugin_settings:\n\n"
                "Plugin settings\n===============\n\n"
                "The plugin can be adjusted using the following settings, "
                "to be found in its settings dialog (|path_to_settings|).\n")
        for groupName, group in grouped.items():
            section_marks = "-" * len(groupName)
            f.write("\n%s\n%s\n\n"
                    ".. list-table::\n"
                    "   :header-rows: 1\n"
                    "   :stub-columns: 1\n"
                    "   :widths: 20 80\n"
                    "   :class: non-responsive\n\n"
                    "   * - Option\n"
                    "     - Description\n"
                    % (groupName, section_marks))
            for setting in group:
                f.write("   * - %s\n"
                        "     - %s\n"
                        % (setting["label"], setting["description"]))


@task
@cmdopts([
    ('clean', 'c', 'clean out built artifacts first'),
    ('sphinx_theme=', 's', 'Sphinx theme to use in documentation'),
])
def builddocs(options):
    try:
        # May fail if not in a git repo
        sh("git submodule init")
        sh("git submodule update")
    except:
        pass
    create_settings_docs(options)
    if getattr(options, 'clean', False):
        options.sphinx.builddir.rmtree()
    if getattr(options, 'sphinx_theme', False):
        # overrides default theme by the one provided in command line
        set_theme = "-D html_theme='{}'".format(options.sphinx_theme)
    else:
        # Uses default theme defined in conf.py
        set_theme = ""
    sh("sphinx-build -a {} {} {}/html".format(set_theme,
                                              options.sphinx.sourcedir,
                                              options.sphinx.builddir))