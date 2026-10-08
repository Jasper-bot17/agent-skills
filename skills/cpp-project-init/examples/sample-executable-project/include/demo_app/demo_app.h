#ifndef DEMO_APP_H
#define DEMO_APP_H

/// @file demo_app.h
/// @brief DemoApp 工具类
/// @author Auto-generated
/// @date 2026

namespace demo_app {

/**
 * @brief 示例工具类
 */
class DemoApp {
public:
    DemoApp() = default;
    ~DemoApp() = default;

    /// @brief 示例方法
    /// @param x 输入值
    /// @return 计算结果
    int add(int x, int y) const;

private:
    int value_ = 0;  ///< 示例成员变量
};

}  // namespace demo_app

#endif  // DEMO_APP_H
