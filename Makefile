SHELL := /bin/bash

SUBDIRS := week9 week10

.PHONY: all clean rebuild $(SUBDIRS)

all: week10 week9

week9:
	$(MAKE) -C week9 all

week10:
	$(MAKE) -C week10 all

clean:
	for dir in $(SUBDIRS); do $(MAKE) -C $$dir clean; done

rebuild: clean all
