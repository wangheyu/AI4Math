/*
 * MNIST MLP C 语言推理
 * ====================
 * 读取 Python 训练导出的权重/偏置文本文件，
 * 对 MNIST 测试样本做前向传播推理。
 *
 * 编译: gcc -o mnist_mlp_infer mnist_mlp_infer.c -lm
 * 运行: ./mnist_mlp_infer samples/sample_0.txt
 *
 * 网络结构: 784 -> 128 -> 64 -> 10
 * 操作: 矩阵乘向量 + 加偏置 + ReLU + argmax
 *
 * 这演示了: 训练完成后，模型 = 固定参数 + 确定性数值计算。
 * 不需要 PyTorch，不需要 GPU，不需要 Python。
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>

/* ── 网络维度常量 ── */
#define INPUT_DIM   784
#define HIDDEN1_DIM 128
#define HIDDEN2_DIM 64
#define OUTPUT_DIM  10

/* ── 读取一行中的浮点数到数组，返回读取个数 ── */
static int read_floats(FILE *fp, float *buf, int max_n) {
    int n = 0;
    while (n < max_n) {
        float val;
        if (fscanf(fp, "%f", &val) != 1) break;
        buf[n++] = val;
    }
    return n;
}

/* ── 跳过注释行 ── */
static void skip_comment(FILE *fp) {
    int c = fgetc(fp);
    if (c == '#') {
        while ((c = fgetc(fp)) != EOF && c != '\n');
    } else if (c != EOF) {
        ungetc(c, fp);
    }
}

/* ── 读取权重矩阵: out_dim 行，每行 in_dim 列 ── */
static float *load_weight(const char *path, int out_dim, int in_dim) {
    FILE *fp = fopen(path, "r");
    if (!fp) { fprintf(stderr, "Cannot open %s\n", path); exit(1); }
    float *w = (float *)malloc(out_dim * in_dim * sizeof(float));
    skip_comment(fp); /* skip header line */
    for (int i = 0; i < out_dim; i++) {
        int n = read_floats(fp, w + i * in_dim, in_dim);
        if (n != in_dim) {
            fprintf(stderr, "%s: row %d expected %d values, got %d\n", path, i, in_dim, n);
            exit(1);
        }
    }
    fclose(fp);
    return w;
}

/* ── 读取偏置向量: out_dim 个值 ── */
static float *load_bias(const char *path, int out_dim) {
    FILE *fp = fopen(path, "r");
    if (!fp) { fprintf(stderr, "Cannot open %s\n", path); exit(1); }
    float *b = (float *)malloc(out_dim * sizeof(float));
    skip_comment(fp);
    int n = read_floats(fp, b, out_dim);
    if (n != out_dim) {
        fprintf(stderr, "%s: expected %d values, got %d\n", path, out_dim, n);
        exit(1);
    }
    fclose(fp);
    return b;
}

/* ── 读取输入图像: 28 行，每行 28 个像素 ── */
static float *load_image(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) { fprintf(stderr, "Cannot open %s\n", path); exit(1); }
    float *img = (float *)malloc(INPUT_DIM * sizeof(float));
    skip_comment(fp); /* skip label comment */
    int n = read_floats(fp, img, INPUT_DIM);
    if (n != INPUT_DIM) {
        fprintf(stderr, "%s: expected %d pixels, got %d\n", path, INPUT_DIM, n);
        exit(1);
    }
    fclose(fp);
    return img;
}

/* ── 线性层: y = W @ x + b ── */
static void linear(const float *w, const float *x, const float *b,
                   float *y, int out_dim, int in_dim) {
    for (int i = 0; i < out_dim; i++) {
        float sum = b[i];
        for (int j = 0; j < in_dim; j++) {
            sum += w[i * in_dim + j] * x[j];
        }
        y[i] = sum;
    }
}

/* ── ReLU 激活: y[i] = max(0, x[i]) ── */
static void relu(float *x, int n) {
    for (int i = 0; i < n; i++) {
        if (x[i] < 0.0f) x[i] = 0.0f;
    }
}

/* ── argmax: 返回最大值的索引 ── */
static int argmax(const float *x, int n) {
    int best = 0;
    for (int i = 1; i < n; i++) {
        if (x[i] > x[best]) best = i;
    }
    return best;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <sample_file>\n", argv[0]);
        return 1;
    }

    /* ── 加载参数 ── */
    printf("Loading parameters...\n");
    float *w1 = load_weight("params/layer1_weight.txt", HIDDEN1_DIM, INPUT_DIM);
    float *b1 = load_bias  ("params/layer1_bias.txt",   HIDDEN1_DIM);
    float *w2 = load_weight("params/layer2_weight.txt", HIDDEN2_DIM, HIDDEN1_DIM);
    float *b2 = load_bias  ("params/layer2_bias.txt",   HIDDEN2_DIM);
    float *w3 = load_weight("params/layer3_weight.txt", OUTPUT_DIM,  HIDDEN2_DIM);
    float *b3 = load_bias  ("params/layer3_bias.txt",   OUTPUT_DIM);

    /* ── 加载输入 ── */
    printf("Loading image: %s\n", argv[1]);
    float *input = load_image(argv[1]);

    /* ── 前向传播 ── */
    float h1[HIDDEN1_DIM];
    float h2[HIDDEN2_DIM];
    float logits[OUTPUT_DIM];

    /* 第 1 层: 784 -> 128 */
    linear(w1, input, b1, h1, HIDDEN1_DIM, INPUT_DIM);
    relu(h1, HIDDEN1_DIM);

    /* 第 2 层: 128 -> 64 */
    linear(w2, h1, b2, h2, HIDDEN2_DIM, HIDDEN1_DIM);
    relu(h2, HIDDEN2_DIM);

    /* 第 3 层: 64 -> 10 */
    linear(w3, h2, b3, logits, OUTPUT_DIM, HIDDEN2_DIM);

    /* ── 预测 ── */
    int pred = argmax(logits, OUTPUT_DIM);

    printf("\nPrediction: %d\n", pred);
    printf("Logits: ");
    for (int i = 0; i < OUTPUT_DIM; i++) {
        printf("%.4f ", logits[i]);
    }
    printf("\n");

    /* ── 释放内存 ── */
    free(w1); free(b1);
    free(w2); free(b2);
    free(w3); free(b3);
    free(input);

    return 0;
}
