SUBDIRS                 =       M2Crypto-0.19.1 \
                                boto-1.7a-patched \
                                euca2ools


all: build install

build:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done

install:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done


clean:
	@for subdir in $(SUBDIRS); do \
                (cd $$subdir && $(MAKE) $@) || exit $$? ; done

