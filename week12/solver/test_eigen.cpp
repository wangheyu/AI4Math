#include <Eigen/Dense>
#include <iostream>
int main() {
    Eigen::Matrix2d A;
    A << 1, 2, 3, 4;
    Eigen::Matrix2d B = A * A;
    std::cout << "Eigen B(0,0)=" << B(0,0) << " (expect 7)" << std::endl;
    return (std::abs(B(0,0) - 7.0) < 0.001) ? 0 : 1;
}
