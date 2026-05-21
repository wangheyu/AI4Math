## 顶层 Makefile — 统一编译/清理/测试 四个子项目
##
## 目标:
##   make all         — 编译所有子目录的 C/C++ 程序 + 讲义 PDF
##   make build       — 同 all
##   make test        — 在每个子目录跑 run_tests.sh
##   make pdf         — 仅编译三份子目录讲义 PDF + 顶层 sparse 讲义
##   make clean       — 删除可执行 / 编译产物 (保留实验结果 / PDF)
##   make distclean   — 同时清除实验结果 / PDF / 数据
##   make status      — 列出各子目录关键产物状态
##   make help        — 本帮助

SUBDIRS = gauss_elimination fdm3d sparse visualization

.PHONY: all build test pdf clean distclean status help \
        $(SUBDIRS) test-each pdf-each clean-each distclean-each

## ----- 主目标 -----

all build: $(SUBDIRS)

$(SUBDIRS):
	@echo ""
	@echo "==================== $@ ===================="
	$(MAKE) -C $@ all

## ----- 测试 -----

test:
	@for d in $(SUBDIRS); do \
		echo ""; echo "==================== test: $$d ===================="; \
		if [ -x $$d/run_tests.sh ]; then \
			( cd $$d && ./run_tests.sh ) || echo "  [$$d] 测试有失败"; \
		else \
			echo "  ($$d 无 run_tests.sh, 跳过)"; \
		fi; \
	done

## ----- 仅 PDF -----

pdf:
	@for d in $(SUBDIRS); do \
		if [ -f $$d/Makefile ] && grep -q "^pdf:" $$d/Makefile 2>/dev/null; then \
			echo ""; echo "[pdf] $$d"; $(MAKE) -C $$d pdf || true; \
		fi; \
	done

## ----- 清理 -----

clean:
	@for d in $(SUBDIRS); do \
		echo "[clean] $$d"; \
		$(MAKE) -C $$d clean || true; \
	done

distclean:
	@for d in $(SUBDIRS); do \
		echo "[distclean] $$d"; \
		$(MAKE) -C $$d distclean 2>/dev/null || $(MAKE) -C $$d clean; \
	done

## ----- 状态总览 -----

status:
	@echo "项目状态:"
	@for d in $(SUBDIRS); do \
		echo ""; echo "  ----- $$d -----"; \
		ls -lh $$d/*.pdf $$d/run_tests.sh $$d/Makefile 2>/dev/null | awk '{printf "    %-30s %s\n",$$NF,$$5}'; \
		echo "    可执行:"; \
		find $$d -maxdepth 1 -type f -executable ! -name "*.sh" ! -name "*.py" ! -name "Makefile" \
			-printf "      %f\n" 2>/dev/null | head -10; \
	done

## ----- 帮助 -----

help:
	@grep -E "^##" $(firstword $(MAKEFILE_LIST)) | sed 's/^## *//'
