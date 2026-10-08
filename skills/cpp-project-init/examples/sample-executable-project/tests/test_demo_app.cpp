#include <gtest/gtest.h>
#include "demo_app/demo_app.h"

TEST(DemoAppTest, AddPositiveNumbers) {
    demo_app::DemoApp obj;
    EXPECT_EQ(obj.add(2, 3), 5);
    EXPECT_EQ(obj.add(0, 0), 0);
}

TEST(DemoAppTest, AddNegativeNumbers) {
    demo_app::DemoApp obj;
    EXPECT_EQ(obj.add(-1, 1), 0);
    EXPECT_EQ(obj.add(-5, -3), -8);
}
