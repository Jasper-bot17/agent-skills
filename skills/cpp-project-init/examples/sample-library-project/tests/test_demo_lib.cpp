#include <gtest/gtest.h>
#include "demo_lib/demo_lib.h"

TEST(DemoLibTest, AddPositiveNumbers) {
    demo_lib::DemoLib obj;
    EXPECT_EQ(obj.add(2, 3), 5);
    EXPECT_EQ(obj.add(0, 0), 0);
}

TEST(DemoLibTest, AddNegativeNumbers) {
    demo_lib::DemoLib obj;
    EXPECT_EQ(obj.add(-1, 1), 0);
    EXPECT_EQ(obj.add(-5, -3), -8);
}
