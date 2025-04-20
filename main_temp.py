
from manim import *

class text_12(Scene):
    def construct(self):
        t1 = Text("धन्यवाद!", font_size=48)
        t1[:].color = YELLOW
        t2 = Text("Like | Share | Subscribe करना न भूलें ❤️", font_size=42)
        t2[:].color = GREEN
        t3 = VGroup(t1, t2)
        t3.arrange(DOWN)
        self.play(Write(t3))
        self.wait(3)
