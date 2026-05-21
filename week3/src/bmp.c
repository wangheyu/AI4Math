#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#pragma pack(push, 1)
typedef struct {
    uint16_t signature;      // BM
    uint32_t fileSize;       // 文件大小
    uint16_t reserved1;      // 保留字段1
    uint16_t reserved2;      // 保留字段2
    uint32_t dataOffset;     // 数据偏移量
} BMPFileHeader;

typedef struct {
    uint32_t headerSize;     // 信息头大小
    int32_t  width;          // 图像宽度
    int32_t  height;         // 图像高度（正数表示倒序）
    uint16_t planes;         // 颜色平面数
    uint16_t bitsPerPixel;   // 每像素位数
    uint32_t compression;    // 压缩方式
    uint32_t imageSize;      // 图像数据大小
    int32_t  xPixelsPerMeter;// 水平分辨率
    int32_t  yPixelsPerMeter;// 垂直分辨率
    uint32_t colorsUsed;     // 使用的颜色数
    uint32_t colorsImportant;// 重要颜色数
} BMPInfoHeader;
#pragma pack(pop)

// 创建24位真彩色BMP图像
void createBMP24(const char* filename, int width, int height, uint8_t* imageData) {
    BMPFileHeader fileHeader;
    BMPInfoHeader infoHeader;
    
    // 计算每行需要的字节数（必须是4的倍数）
    int rowSize = (width * 3 + 3) & ~3;
    int dataSize = rowSize * height;
    int fileSize = sizeof(BMPFileHeader) + sizeof(BMPInfoHeader) + dataSize;
    
    // 填充文件头
    fileHeader.signature = 0x4D42;  // "BM"
    fileHeader.fileSize = fileSize;
    fileHeader.reserved1 = 0;
    fileHeader.reserved2 = 0;
    fileHeader.dataOffset = sizeof(BMPFileHeader) + sizeof(BMPInfoHeader);
    
    // 填充信息头
    infoHeader.headerSize = sizeof(BMPInfoHeader);
    infoHeader.width = width;
    infoHeader.height = -height;  // 负数表示正向存储（从上到下）
    infoHeader.planes = 1;
    infoHeader.bitsPerPixel = 24;
    infoHeader.compression = 0;
    infoHeader.imageSize = dataSize;
    infoHeader.xPixelsPerMeter = 2835;  // 72 DPI
    infoHeader.yPixelsPerMeter = 2835;  // 72 DPI
    infoHeader.colorsUsed = 0;
    infoHeader.colorsImportant = 0;
    
    // 写入文件
    FILE* file = fopen(filename, "wb");
    if (!file) {
        printf("无法创建文件: %s\n", filename);
        return;
    }
    
    fwrite(&fileHeader, sizeof(BMPFileHeader), 1, file);
    fwrite(&infoHeader, sizeof(BMPInfoHeader), 1, file);
    
    // 写入像素数据
    for (int y = 0; y < height; y++) {
        fwrite(imageData + y * width * 3, 1, width * 3, file);
        // 写入行填充字节
        int padding = rowSize - width * 3;
        uint8_t pad[3] = {0, 0, 0};
        fwrite(pad, 1, padding, file);
    }
    
    fclose(file);
    printf("BMP图像已创建: %s\n", filename);
}

// 生成渐变图像示例
void generateGradient(const char* filename, int width, int height) {
    uint8_t* imageData = (uint8_t*)malloc(width * height * 3);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int index = (y * width + x) * 3;
            // 创建从红到蓝的渐变
            imageData[index] = (uint8_t)(255 * x / width);        // 蓝色分量
            imageData[index + 1] = (uint8_t)(255 * (1 - (float)y / height)); // 绿色分量
            imageData[index + 2] = (uint8_t)(255 * y / height);   // 红色分量
        }
    }
    
    createBMP24(filename, width, height, imageData);
    free(imageData);
}

// 生成彩色条纹图像
void generateStripes(const char* filename, int width, int height) {
    uint8_t* imageData = (uint8_t*)malloc(width * height * 3);
    int stripeWidth = width / 7;  // 7种颜色条纹
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int index = (y * width + x) * 3;
            int stripe = x / stripeWidth;
            
            switch (stripe) {
                case 0: // 红色
                    imageData[index] = 0;
                    imageData[index + 1] = 0;
                    imageData[index + 2] = 255;
                    break;
                case 1: // 橙色
                    imageData[index] = 0;
                    imageData[index + 1] = 165;
                    imageData[index + 2] = 255;
                    break;
                case 2: // 黄色
                    imageData[index] = 0;
                    imageData[index + 1] = 255;
                    imageData[index + 2] = 255;
                    break;
                case 3: // 绿色
                    imageData[index] = 0;
                    imageData[index + 1] = 255;
                    imageData[index + 2] = 0;
                    break;
                case 4: // 青色
                    imageData[index] = 255;
                    imageData[index + 1] = 255;
                    imageData[index + 2] = 0;
                    break;
                case 5: // 蓝色
                    imageData[index] = 255;
                    imageData[index + 1] = 0;
                    imageData[index + 2] = 0;
                    break;
                case 6: // 紫色
                    imageData[index] = 255;
                    imageData[index + 1] = 0;
                    imageData[index + 2] = 128;
                    break;
                default:
                    imageData[index] = 0;
                    imageData[index + 1] = 0;
                    imageData[index + 2] = 0;
            }
        }
    }
    
    createBMP24(filename, width, height, imageData);
    free(imageData);
}

// 生成棋盘格图案
void generateCheckerboard(const char* filename, int width, int height) {
    uint8_t* imageData = (uint8_t*)malloc(width * height * 3);
    int squareSize = 50;  // 方格大小
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int index = (y * width + x) * 3;
            int isEven = ((x / squareSize) + (y / squareSize)) % 2;
            
            if (isEven == 0) {
                // 白色
                imageData[index] = 255;
                imageData[index + 1] = 255;
                imageData[index + 2] = 255;
            } else {
                // 深灰色
                imageData[index] = 64;
                imageData[index + 1] = 64;
                imageData[index + 2] = 64;
            }
        }
    }
    
    createBMP24(filename, width, height, imageData);
    free(imageData);
}

// 生成简单的几何图形
void generateShapes(const char* filename, int width, int height) {
    uint8_t* imageData = (uint8_t*)malloc(width * height * 3);
    
    // 先填充白色背景
    for (int i = 0; i < width * height * 3; i += 3) {
        imageData[i] = 255;     // 蓝色
        imageData[i + 1] = 255; // 绿色
        imageData[i + 2] = 255; // 红色
    }
    
    // 绘制一个红色圆
    int centerX = width / 4;
    int centerY = height / 2;
    int radius = height / 4;
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int dx = x - centerX;
            int dy = y - centerY;
            if (dx * dx + dy * dy <= radius * radius) {
                int index = (y * width + x) * 3;
                imageData[index] = 0;      // 蓝色
                imageData[index + 1] = 0;  // 绿色
                imageData[index + 2] = 255; // 红色
            }
        }
    }
    
    // 绘制一个蓝色矩形
    int rectX = width * 2 / 3;
    int rectY = height / 4;
    int rectWidth = width / 6;
    int rectHeight = height / 2;
    
    for (int y = rectY; y < rectY + rectHeight && y < height; y++) {
        for (int x = rectX; x < rectX + rectWidth && x < width; x++) {
            int index = (y * width + x) * 3;
            imageData[index] = 255;    // 蓝色
            imageData[index + 1] = 0;  // 绿色
            imageData[index + 2] = 0;  // 红色
        }
    }
    
    createBMP24(filename, width, height, imageData);
    free(imageData);
}

int main() {
    int width = 800;
    int height = 600;
    
    printf("开始生成BMP图像...\n\n");
    
    // 生成不同的示例图像
    generateGradient("gradient.bmp", width, height);
    generateStripes("stripes.bmp", width, height);
    generateCheckerboard("checkerboard.bmp", width, height);
    generateShapes("shapes.bmp", width, height);
    
    printf("\n所有图像生成完成！\n");
    printf("生成的文件：\n");
    printf("  - gradient.bmp (渐变图像)\n");
    printf("  - stripes.bmp (彩色条纹)\n");
    printf("  - checkerboard.bmp (棋盘格)\n");
    printf("  - shapes.bmp (几何图形)\n");
    
    return 0;
}