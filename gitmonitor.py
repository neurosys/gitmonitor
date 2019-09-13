#!/bin/python3

import subprocess
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

pathToRepo = '/opt/work/tus/tracking/.git'

GIT_LOG_SHORT_FORMAT = "short"
GIT_LOG_FORMATS = {
        GIT_LOG_SHORT_FORMAT: ['git', 'log', '--date=short', '--pretty=format:%h %cd [%cn] %s{$$$}'],
        "extra": ['git', 'log', '--date=short', '--pretty=format:%h %cd [%cn] {{%d}} %s{$$$}'],
        }

class CommitLine():
    def __init__(self, line, logFormat):
        self.line = line
        self._splitLine(line, logFormat)

    def __str__(self):
        return self.shortId + " " + self.date + " " + self.author + " " + self.msg

    def getArrayInfo(self):
        return (self.shortId, self.date, self.author, self.msg)

    def getLine(self):
        return self.line

    def _splitLine(self, line, logFormat):
        if logFormat == GIT_LOG_SHORT_FORMAT:
            self._splitShortFormat(line)
            
    def _splitShortFormat(self, line):
        #print(line)
        self.shortId = line[0 : 7]
        self.date = line[9 : 18]
        endOfAuthorName = line.find("]", 21)
        self.author = line[20 : endOfAuthorName]
        self.msg = line[endOfAuthorName + 2 : ]
        #print("shortId = " + self.shortId)
        #print("date = " + self.date)
        #print("author = " + self.author)
        #print("msg = '" + self.msg + "'")

    def buildCommitsFromLines(outputBlock, logFormat):
        lines = outputBlock.split("{$$$}")
        commits = []
        for line in lines:
            line = line.strip()
            if line != "":
                commits.append(CommitLine(line, logFormat))
        return commits


    def getShortLineFormat(formatName):
        cmd = GIT_LOG_FORMATS[formatName]
        return cmd

class RepoHandler():
    def __init__(self, localPathToRepo):
        self.localPathToRepo = localPathToRepo

    def clone(self):
        pass

    def pull(self, remotePathToRepo):
        cmd = ['git', 'pull']
        self._gitCmdExecutor(cmd)
        pass

    def log(self):
        cmd = CommitLine.getShortLineFormat(GIT_LOG_SHORT_FORMAT)
        logOutput = self._gitCmdExecutor(cmd)
        return CommitLine.buildCommitsFromLines(logOutput, GIT_LOG_SHORT_FORMAT)
        #print(logOutput)

    def branch(self):
        pass

    def _gitCmdExecutor(self, cmd):
        currentWorkDir = os.getcwd()
        os.chdir(self.localPathToRepo)
        output = subprocess.check_output(cmd)
        os.chdir(currentWorkDir)
        return output.decode("utf-8")


repo = RepoHandler(pathToRepo)

commits = repo.log()

commitList = []

for commit in commits:
    commitList.append(commit.getArrayInfo())
    #print(commit)

class TreeViewFilterWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="List of commits")
        self.set_border_width(10)

        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        #Creating the ListStore model
        self.software_liststore = Gtk.ListStore(str, str, str, str)
        for software_ref in commitList:
            self.software_liststore.append(list(software_ref))
        self.current_filter_language = None

        #Creating the filter, feeding it with the liststore model
        self.language_filter = self.software_liststore.filter_new()
        #setting the filter function, note that we're not using the
        self.language_filter.set_visible_func(self.language_filter_func)

        #creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView.new_with_model(self.language_filter)
        for i, column_title in enumerate(["ID", "Date", "Author", "Message"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        #creating buttons to filter by programming language, and setting up their events
        self.buttons = list()
        for prog_language in ["Java", "C", "C++", "Python", "None"]:
            button = Gtk.Button(label=prog_language)
            self.buttons.append(button)
            button.connect("clicked", self.on_selection_button_clicked)

        #setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 8, 10)
        self.grid.attach_next_to(self.buttons[0], self.scrollable_treelist, Gtk.PositionType.BOTTOM, 1, 1)
        for i, button in enumerate(self.buttons[1:]):
            self.grid.attach_next_to(button, self.buttons[i], Gtk.PositionType.RIGHT, 1, 1)
        self.scrollable_treelist.add(self.treeview)

        self.show_all()

    def language_filter_func(self, model, iter, data):
        """Tests if the language in the row is the one in the filter"""
        if self.current_filter_language is None or self.current_filter_language == "None":
            return True
        else:
            return model[iter][2] == self.current_filter_language

    def on_selection_button_clicked(self, widget):
        """Called on any of the button clicks"""
        #we set the current language filter to the button's label
        self.current_filter_language = widget.get_label()
        print("%s language selected!" % self.current_filter_language)
        #we update the filter, which updates in turn the view
        self.language_filter.refilter()


win = TreeViewFilterWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
