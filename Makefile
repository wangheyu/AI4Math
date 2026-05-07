SHELL := /bin/bash

SUBDIRS := final_project/Qian week10 week9

.PHONY: all clean rebuild $(SUBDIRS)

all: final_project/Qian week10 week9

final_project/Qian:
	$(MAKE) -C final_project/Qian all

week9:
	$(MAKE) -C week9 all

week10:
	$(MAKE) -C week10 all

clean:
	for dir in $(SUBDIRS); do $(MAKE) -C $$dir clean; done

rebuild: clean all
