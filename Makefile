#!/usr/bin/make -f
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Neil Soman neil@eucalyptus.com

SUBDIRS                 =       euca2ools
BINDIR			=	bin
BINLIST			=	$(wildcard $(BINDIR)/*)
MANDIR			=	man
MANPAGES		=	$(shell echo $(BINLIST) | sed -e 's%$(BINDIR)/%$(MANDIR)/%g' -e 's/  */.1 /g').1
PREFIX			=	/usr/local
BASH_COMPLETION		=	/etc/bash_completion.d
UTILDIR			=	util
 
.PHONY: man all install clean distclean

all: install

man: $(BINLIST)
	@echo "Re-generating manpages..."
	@which help2man > /dev/null || { echo "You'll need to install help2man to re-generate the manpages"; exit 1; }
	@mkdir -p $(MANDIR);
	@rm -rf $(MANDIR)/*;
	@export PYTHONPATH=$(CURDIR)$${PYTHONPATH:+:${PYTHONPATH}}; \
	    for x in $(BINLIST); do echo "  $${x##*/}"; \
	        DESCR=`$$x --help | head -n2 | tail -n1`; \
	        help2man $$x -N -o "$(MANDIR)/$${x##*/}.1" -n "Eucalyptus tool: $${DESCR}  " || exit; \
	    done

install:
	python setup.py install
	@install -o root -m 755 -d $(PREFIX)/man/man1
	@if [ -d $(MANDIR) ]; then install -o root -m 644  $(MANDIR)/* $(PREFIX)/man/man1; fi
	@if [ -d $(BASH_COMPLETION) ]; then install -o root -m 644  $(UTILDIR)/* $(BASH_COMPLETION); fi
 
distclean clean:
	@for subdir in $(SUBDIRS); do \
		(cd $$subdir && $(MAKE) $@) || exit $$? ; done

uninstall:
	@for x in $(BINLIST); do \
		rm -f $(PREFIX)/bin/$$x ; \
		rm -f $(PREFIX)/man/man1/`basename $$x`.1; done
	@if [ -d $(BASH_COMPLETION) ]; then rm $(BASH_COMPLETION)/euca2ools; fi 
