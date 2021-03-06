#!/usr/bin/env python
# Author: Sharpe

import optparse
import time
import threading
from threading import Thread

class UNC:

    def __init__(self, infile, outfile, numberadd, useroptions):
        self.infile = infile
        self.outfile = outfile
        self.common_substitutions_file = "common_substitutions.txt"
        self.common_substitutions_dict = self.parseCommonSubsToDict()
        self.createEmptyFile()
        self.numberadd = numberadd
        self.casesense = useroptions.casesense
        self.specialchars = useroptions.specialchars
        self.lock = threading.Lock()
        # https://www.owasp.org/index.php?title=Testing_for_Default_or_Guessable_User_Account_(OWASP-AT-003)&setlang=es
        self.defaultList = ["admin", "administrator", "root", "system", "guest", "operator", "super"]

    def createEmptyFile(self):
        open(self.outfile, 'w').close()

    def createOptions(self, user, casesense_run = False):
        firstname, secondname = user.strip().split(" ")
        if self.casesense and not casesense_run:
            """If case sensitive is set, repeat the process for also only non capitalized input"""
            self.createOptions(user.lower(), True)
        options = self.applyOptionRules(firstname, secondname)
        if self.numberadd >= 0:
            options = options + self.addNumbersToOptions(options, self.numberadd)
        if self.specialchars:
            options = options + self.specialCharsSubstitute(options)
        self.lock.acquire()
        with open(self.outfile, 'a') as f:
            for username in options:
                f.write(username + "\n")
        self.lock.release()

    def applyOptionRules(self, firstname, secondname):
        options = []
        options.append(firstname)
        options.append(secondname)
        options.append(firstname + secondname)
        options.append(firstname + '.' + secondname)
        options.append(firstname[0] + secondname)
        options.append(firstname[0] + '.' + secondname)
        options.append(secondname + firstname)
        options.append(secondname + firstname[0])
        options.append(secondname[0] + firstname)

        return options

    def addNumbersToOptions(self, options, mrange):
        optionsWithNumbers = []
        for option in options:
            optionsWithNumbers = optionsWithNumbers + self.addNumbersToUsername(mrange, option)
        return optionsWithNumbers

    def addNumbersToUsername(self, mrange, username):
        numberedUsernames = []
        if mrange > 0:
            for i in range(0, mrange+1):
                numberedUsernames.append(username + str(i))
        return numberedUsernames

    def parseCommonSubsToDict(self):
        d = {}
        with open(self.common_substitutions_file, 'r') as f:
            for line in f:
                (key, val) = line.strip().split('=')
                d[key] = val
        return d

    def specialCharsSubstitute(self, userlist):
        newlist = []
        for user in userlist:
            for (char, sub) in self.common_substitutions_dict.items():
                try:
                    newlist.append(user.replace(char, sub))
                except e:
                    pass
        return newlist



    def run(self):
        threads = []
        with open(self.infile, 'r') as userfile:
            for user in userfile:
                if user == "\n":
                    pass
                else:
                    t = Thread(target=self.createOptions, args=[user])
                    threads.append(t)
                    t.start()
        print("[*] {} threads started".format(len(threads)))
        for t in threads:
            t.join()
        print('[+] List creation finished: {}'.format(self.outfile))


def main():
    parser = optparse.OptionParser(usage='usage: '+__file__+ ' -i inputfile [-oncs]')
    parser.add_option('-i', '--inputfile', dest='infile', type='string', help='Specify a file containing a list of first and second names (e.g. John Doe)')
    parser.add_option('-o', '--outputfile', dest='outfile', type='string', help='Specify an outputfile, otherwise a custom name will be created')
    parser.add_option('-n', '--numberadd', dest='numberadd', type='string', help='Additionally create usernames with appended number, default is no number')
    parser.add_option('-c', '--casesensitive', dest='casesense', action="store_true", default=False, help='Use this if you want case sensitivity activated, this will result in a list that is two times the size, default=False')
    parser.add_option('-s', '--specialchars', dest='specialchars', action="store_true", default=False, help='Use this if you want special chars in names e.g. a=@')

    (options, args) = parser.parse_args()
    if options.infile == None:
        print('[-] No inputfile specified')
        print(parser.usage())
        exit(0)
    if options.outfile == None:
        outfile = "usernames_" + time.strftime("%Y%m%d-%H%M%S")
        print('[-] No outputfile specified, creating default file {}'.format(outfile))
    else:
        outfile = options.outfile
    if options.numberadd == None:
        numberadd = -1
    else:
        numberadd = int(options.numberadd)

    print('[+] Starting creating username file')
    unc = UNC(options.infile, outfile, numberadd, options)
    unc.run()


if __name__ == "__main__":
    main()
