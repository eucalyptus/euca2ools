SUBDIRS                 =       euca2ools 

all: build install

build:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done

install:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done
	@install -g root -o root -m 755 -d /usr/local/install
	@install -g root -o root -m 755  bin/* /usr/local/bin/

clean:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done

