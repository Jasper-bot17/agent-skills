#ifndef DEMO_LIB_H
#define DEMO_LIB_H

/// @file demo_lib.h
/// @brief DemoLib 工具类
/// @author Auto-generated
/// @date 2026

namespace demo_lib {

/**
 * @brief 示例工具类
 */
class DemoLib {
public:
    DemoLib() = default;
    ~DemoLib() = default;

    /// @brief 示例方法
    /// @param x 输入值
    /// @return 计算结果
    int add(int x, int y) const;

private:
    int value_ = 0;  ///< 示例成员变量
};

}  // namespace demo_lib

#endif  // DEMO_LIB_H
