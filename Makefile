SUBDIRS                 =       euca2ools
BINLIST			=	`ls bin`
MANDIR			=	man

all: build man install

build:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done

man:
	@echo "Generating manpages..."
	mkdir -p $(MANDIR) 
	@for x in $(BINLIST); do \
		help2man bin/$$x -o $(MANDIR)/$$x.1 ; done

install: build man
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done
	@install -g root -o root -m 755 -d /usr/local/bin
	@install -g root -o root -m 755  bin/* /usr/local/bin/
	@install -g root -o root -m 755 -d /usr/local/man/man1
	@install -g root -o root -m 644  $(MANDIR)/* /usr/local/man/man1
 
clean:
	@for subdir in $(SUBDIRS); do \
		(cd $$subdir && $(MAKE) $@) || exit $$? ; done
	rm -rf $(MANDIR) 

uninstall: man
	@for x in $(BINLIST); do \
		rm -f /usr/local/bin/$$x ; done
	@for x in `ls $(MANDIR)`; do \
		rm -f /usr/local/man/man1/$$x ; done
	
