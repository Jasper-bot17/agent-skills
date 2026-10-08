#include <iostream>
#include "demo_app/demo_app.h"

int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;

    demo_app::DemoApp app;
    std::cout << "demo-app v1.0.0" << std::endl;
    std::cout << "2 + 3 = " << app.add(2, 3) << std::endl;

    return 0;
}
