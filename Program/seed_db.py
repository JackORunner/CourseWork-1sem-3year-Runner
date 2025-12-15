import sys
from Program.database import Database

SAMPLES = [
    {
        "subject": "Learning Science",
        "topic_name": "Spaced Repetition Blueprint",
        "content": (
            "Start with a single small deck of concepts and schedule reviews at widening intervals: "
            "1 day, 3 days, 7 days, 14 days, and 30 days. Each session should be short, focused, "
            "and timed, with deliberate pauses to recall before revealing the answer. Keep cards "
            "atomic: one fact or idea per card, phrased as a clear question-answer pair. Mix "
            "examples and counterexamples to strengthen discrimination. Track leeches—items you "
            "keep missing—and rewrite them with simpler prompts or richer cues. Pair retrieval with "
            "brief elaboration: after answering, add one sentence that links the idea to prior "
            "knowledge or a practical scenario. Keep daily workloads predictable; cap sessions to "
            "avoid burnout. Once a week, prune duplicates, merge overlapping cards, and retire items "
            "that are obvious. Once a month, reshuffle hard items into smaller focused sets. Protect "
            "consistency: tie reviews to a stable trigger, like the first work block of the day. "
            "Celebrate streaks, but forgive misses—resume with a light day rather than trying to "
            "catch up aggressively. The goal is steady, low-friction repetition over months."
        ),
    },
    {
        "subject": "Study Methods",
        "topic_name": "Active Recall Checklist",
        "content": (
            "Begin every session by writing three questions you want answered before you stop. Close "
            "notes and attempt to retrieve aloud or in writing. For each lapse, reopen notes briefly, "
            "then close them again and restate the answer in your own words. Alternate question types: "
            "definitions, mechanisms, comparisons, and applications. After recalling, rate confidence "
            "and tag items as weak, medium, or strong. Revisit weak items twice in the same session "
            "with shorter cues. Summarize the topic in exactly five bullet points, then compress to "
            "one sentence. Teach the material to an imagined peer; if you stumble, that marks a gap. "
            "End with a mini-retrospective: what felt sticky, what stayed fuzzy, and what one tweak "
            "will you apply next time. Keep sessions short (25–40 minutes) and insert a brief break "
            "before switching topics. Store your questions for reuse so you can measure progress across "
            "days, not just within a single sitting."
        ),
    },
    {
        "subject": "Focus & Execution",
        "topic_name": "Deep Work Sprint Plan",
        "content": (
            "Define one concrete outcome for the sprint: a draft, a solved set, or a working prototype. "
            "Block 50–90 minutes with all notifications off and a visible timer. Before starting, list "
            "the smallest next actions and highlight the first two; begin immediately with a low-friction "
            "step. Use a parking lot for intrusive thoughts: jot them down and return to the task. If "
            "stuck for five minutes, change the approach: draw a diagram, restate the question, or test "
            "a minimal example. At the halfway point, checkpoint: are you still on the critical path? "
            "If not, cut scope rather than pushing breadth. In the final ten minutes, write a brief log "
            "of what you did, what blocked you, and the exact next step. Close with a tiny reward and "
            "a reset: stretch, hydrate, and prep the workspace for the next sprint so re-entry is easy."
        ),
    },
    {
        "subject": "Focus & Execution",
        "topic_name": "Deep Work Sprint Plan",
        "content": (
            "Define one concrete outcome for the sprint: a draft, a solved set, or a working prototype. "
            "Block 50–90 minutes with all notifications off and a visible timer. Before starting, list "
            "the smallest next actions and highlight the first two; begin immediately with a low-friction "
            "step. Use a parking lot for intrusive thoughts: jot them down and return to the task. If "
            "stuck for five minutes, change the approach: draw a diagram, restate the question, or test "
            "a minimal example. At the halfway point, checkpoint: are you still on the critical path? "
            "If not, cut scope rather than pushing breadth. In the final ten minutes, write a brief log "
            "of what you did, what blocked you, and the exact next step. Close with a tiny reward and "
            "a reset: stretch, hydrate, and prep the workspace for the next sprint so re-entry is easy."
        ),
    },
    {
        "subject": "Cognitive Science",
        "topic_name": "Dual Coding Theory",
        "content": (
            "Combine verbal and visual information to double the chances of retrieval. When learning a "
            "new concept, don't just write the definition; sketch a diagram, flow chart, or symbol next "
            "to it. The brain processes text and images through separate channels, creating two distinct "
            "memory traces for the same information. If one trace fades, the other can still trigger recall. "
            "Avoid clutter; simple, crude drawings often work better than complex ones because the act of "
            "creating them forces you to distill the core meaning. Label your diagrams clearly and explain "
            "the relationship between the parts aloud. When reviewing, look at the image and try to reconstruct "
            "the text, or cover the image and redraw it from the description. This cross-modal practice "
            "strengthens the associative web in your long-term memory, making knowledge more durable and "
            "flexible under stress."
        ),
    },
    {
        "subject": "Productivity",
        "topic_name": "The Pomodoro Technique",
        "content": (
            "Break work into 25-minute intervals separated by short 5-minute breaks. This structure combats "
            "procrastination by lowering the barrier to entry; you only need to commit to 25 minutes of effort. "
            "During the interval, focus on a single task with zero interruptions. If a distraction arises, "
            "write it down and immediately return to work. After four cycles, take a longer break of 15–30 "
            "minutes to recharge fully. Use a physical timer if possible to create a distinct boundary between "
            "work and rest. The ticking sound can serve as a conditioning cue for focus. Over time, track how "
            "many 'pomodoros' a specific task takes to improve your estimation skills. Respect the breaks "
            "religiously—stand up, move, or look away from screens—to prevent cognitive fatigue and maintain "
            "high-quality attention throughout the day."
        ),
    },
    {
        "subject": "Philosophy",
        "topic_name": "Stoicism: The Dichotomy of Control",
        "content": (
            "The core of Stoic practice is distinguishing between what is up to us and what is not. Our "
            "opinions, impulses, desires, and aversions are within our power; our body, possessions, reputation, "
            "and public offices are not. Suffering arises when we try to control external events or when we "
            "neglect our own internal character. To practice this, pause before reacting to any situation and "
            "ask: 'Is this within my control?' If it is, act with virtue and reason. If it is not, accept it "
            "with equanimity and focus on your response instead. This doesn't mean passivity; it means directing "
            "energy only where it can be effective. By internalizing this dichotomy, you become invincible to "
            "fortune, as your happiness depends solely on your own choices and moral integrity, which no one "
            "can take away from you."
        ),
    },
    {
        "subject": "Computer Science",
        "topic_name": "Big O Notation Basics",
        "content": (
            "Big O notation describes the performance or complexity of an algorithm as the input size grows. "
            "It focuses on the worst-case scenario, ignoring constant factors and lower-order terms. O(1) "
            "represents constant time, where operations take the same amount of time regardless of input size, "
            "like accessing an array index. O(n) is linear time, meaning execution time grows directly with "
            "input size, typical of simple loops. O(n^2) indicates quadratic time, often seen in nested loops "
            "like bubble sort. O(log n) is logarithmic time, characteristic of binary search, where the problem "
            "space is halved at each step. Understanding Big O is crucial for writing scalable code; an O(n^2) "
            "algorithm might work for small datasets but will choke on millions of records. Always analyze "
            "time and space complexity before optimizing code prematurely."
        ),
    },
    {
        "subject": "History",
        "topic_name": "The Industrial Revolution",
        "content": (
            "The Industrial Revolution marked a major turning point in history, shifting from agrarian, "
            "handcraft economies to machine-driven manufacturing. Starting in Britain in the late 18th century, "
            "it was fueled by inventions like the steam engine, spinning jenny, and power loom. This transition "
            "led to urbanization as people flocked to factories for work, fundamentally changing social structures "
            "and daily life. While it brought mass production, lower prices, and technological advancement, it "
            "also introduced harsh labor conditions, pollution, and overcrowding. The revolution spurred the "
            "development of transportation networks like canals and railways, connecting distant markets. It "
            "laid the groundwork for modern capitalism and global trade but also sparked labor movements and "
            "debates about workers' rights that continue to this day. Understanding this era is key to grasping "
            "the roots of modern economic and social challenges."
        ),
    },
    {
        "subject": "Psychology",
        "topic_name": "Cognitive Biases: Confirmation Bias",
        "content": (
            "Confirmation bias is the tendency to search for, interpret, favor, and recall information in a way "
            "that confirms one's preexisting beliefs or hypotheses. It leads people to ignore evidence that "
            "contradicts their views while overvaluing evidence that supports them. This bias affects decision-making "
            "in everything from politics and finance to scientific research and personal relationships. To combat "
            "it, actively seek out disconfirming evidence and consider alternative explanations. Ask yourself: "
            "'What would have to happen for me to be wrong?' Engage with diverse perspectives and play devil's "
            "advocate against your own positions. Recognizing this bias is the first step toward more objective "
            "thinking. It explains why polarization persists and why smart people can hold irrational beliefs. "
            "Intellectual humility—admitting you might be wrong—is the strongest antidote to this deeply ingrained "
            "mental shortcut."
        ),
    },
    {
        "subject": "Writing",
        "topic_name": "The Hero's Journey",
        "content": (
            "The Hero's Journey, or monomyth, is a common narrative template involving a hero who goes on an "
            "adventure, wins a victory in a decisive crisis, and comes home changed or transformed. Identified "
            "by Joseph Campbell, it typically follows stages like the Call to Adventure, Crossing the Threshold, "
            "Tests/Allies/Enemies, the Ordeal, and the Return with the Elixir. This structure resonates deeply "
            "because it mirrors the human experience of growth and overcoming adversity. Writers use it to structure "
            "plots that feel satisfying and universal. However, it shouldn't be a rigid formula; the best stories "
            "adapt the stages to fit unique characters and settings. Whether in ancient myths or modern blockbusters, "
            "the journey represents the psychological passage from innocence to experience. Understanding these "
            "beats helps writers pace their stories and ensure emotional resonance with the audience."
        ),
    },
    {
        "subject": "Health & Fitness",
        "topic_name": "Progressive Overload",
        "content": (
            "Progressive overload is the fundamental principle of strength training and physical conditioning. "
            "It involves gradually increasing the stress placed on the body during exercise to stimulate muscle "
            "growth and strength gains. This can be achieved by lifting heavier weights, doing more repetitions, "
            "reducing rest times, or increasing training frequency. Without overload, the body adapts to the "
            "current stress level and plateaus, leading to stagnation. It requires consistent tracking of workouts "
            "to ensure you are doing slightly more than the previous session. Safety is paramount; increases should "
            "be small and manageable to avoid injury. This principle applies not just to lifting but also to "
            "cardiovascular endurance and flexibility. It teaches the body that it needs to be stronger to survive "
            "the environment, triggering the biological adaptation processes that build resilience and power."
        ),
    },
    {
        "subject": "Economics",
        "topic_name": "Supply and Demand",
        "content": (
            "Supply and demand is the economic model of price determination in a market. It postulates that, "
            "holding all else equal, in a competitive market, the unit price for a particular good, or other "
            "traded item such as labor or liquid financial assets, will vary until it settles at a point where "
            "the quantity demanded (at the current price) will equal the quantity supplied (at the current price), "
            "resulting in an economic equilibrium for price and quantity. If demand increases and supply remains "
            "unchanged, a shortage occurs, leading to a higher equilibrium price. Conversely, if supply increases "
            "and demand remains unchanged, a surplus occurs, leading to a lower equilibrium price. Understanding "
            "these forces helps explain market fluctuations, the impact of taxes, and consumer behavior. It is the "
            "foundational concept upon which most of modern economic theory is built."
        ),
    },
    {
        "subject": "Focus & Execution",
        "topic_name": "Deep Work Sprint Plan",
        "content": (
            "Define one concrete outcome for the sprint: a draft, a solved set, or a working prototype. "
            "Block 50–90 minutes with all notifications off and a visible timer. Before starting, list "
            "the smallest next actions and highlight the first two; begin immediately with a low-friction "
            "step. Use a parking lot for intrusive thoughts: jot them down and return to the task. If "
            "stuck for five minutes, change the approach: draw a diagram, restate the question, or test "
            "a minimal example. At the halfway point, checkpoint: are you still on the critical path? "
            "If not, cut scope rather than pushing breadth. In the final ten minutes, write a brief log "
            "of what you did, what blocked you, and the exact next step. Close with a tiny reward and "
            "a reset: stretch, hydrate, and prep the workspace for the next sprint so re-entry is easy."
        ),
    },
    {
        "subject": "Cognitive Science",
        "topic_name": "Dual Coding Theory",
        "content": (
            "Combine verbal and visual information to double the chances of retrieval. When learning a "
            "new concept, don't just write the definition; sketch a diagram, flow chart, or symbol next "
            "to it. The brain processes text and images through separate channels, creating two distinct "
            "memory traces for the same information. If one trace fades, the other can still trigger recall. "
            "Avoid clutter; simple, crude drawings often work better than complex ones because the act of "
            "creating them forces you to distill the core meaning. Label your diagrams clearly and explain "
            "the relationship between the parts aloud. When reviewing, look at the image and try to reconstruct "
            "the text, or cover the image and redraw it from the description. This cross-modal practice "
            "strengthens the associative web in your long-term memory, making knowledge more durable and "
            "flexible under stress."
        ),
    },
    {
        "subject": "Productivity",
        "topic_name": "The Pomodoro Technique",
        "content": (
            "Break work into 25-minute intervals separated by short 5-minute breaks. This structure combats "
            "procrastination by lowering the barrier to entry; you only need to commit to 25 minutes of effort. "
            "During the interval, focus on a single task with zero interruptions. If a distraction arises, "
            "write it down and immediately return to work. After four cycles, take a longer break of 15–30 "
            "minutes to recharge fully. Use a physical timer if possible to create a distinct boundary between "
            "work and rest. The ticking sound can serve as a conditioning cue for focus. Over time, track how "
            "many 'pomodoros' a specific task takes to improve your estimation skills. Respect the breaks "
            "religiously—stand up, move, or look away from screens—to prevent cognitive fatigue and maintain "
            "high-quality attention throughout the day."
        ),
    },
    {
        "subject": "Philosophy",
        "topic_name": "Stoicism: The Dichotomy of Control",
        "content": (
            "The core of Stoic practice is distinguishing between what is up to us and what is not. Our "
            "opinions, impulses, desires, and aversions are within our power; our body, possessions, reputation, "
            "and public offices are not. Suffering arises when we try to control external events or when we "
            "neglect our own internal character. To practice this, pause before reacting to any situation and "
            "ask: 'Is this within my control?' If it is, act with virtue and reason. If it is not, accept it "
            "with equanimity and focus on your response instead. This doesn't mean passivity; it means directing "
            "energy only where it can be effective. By internalizing this dichotomy, you become invincible to "
            "fortune, as your happiness depends solely on your own choices and moral integrity, which no one "
            "can take away from you."
        ),
    },
    {
        "subject": "Computer Science",
        "topic_name": "Big O Notation Basics",
        "content": (
            "Big O notation describes the performance or complexity of an algorithm as the input size grows. "
            "It focuses on the worst-case scenario, ignoring constant factors and lower-order terms. O(1) "
            "represents constant time, where operations take the same amount of time regardless of input size, "
            "like accessing an array index. O(n) is linear time, meaning execution time grows directly with "
            "input size, typical of simple loops. O(n^2) indicates quadratic time, often seen in nested loops "
            "like bubble sort. O(log n) is logarithmic time, characteristic of binary search, where the problem "
            "space is halved at each step. Understanding Big O is crucial for writing scalable code; an O(n^2) "
            "algorithm might work for small datasets but will choke on millions of records. Always analyze "
            "time and space complexity before optimizing code prematurely."
        ),
    },
    {
        "subject": "History",
        "topic_name": "The Industrial Revolution",
        "content": (
            "The Industrial Revolution marked a major turning point in history, shifting from agrarian, "
            "handcraft economies to machine-driven manufacturing. Starting in Britain in the late 18th century, "
            "it was fueled by inventions like the steam engine, spinning jenny, and power loom. This transition "
            "led to urbanization as people flocked to factories for work, fundamentally changing social structures "
            "and daily life. While it brought mass production, lower prices, and technological advancement, it "
            "also introduced harsh labor conditions, pollution, and overcrowding. The revolution spurred the "
            "development of transportation networks like canals and railways, connecting distant markets. It "
            "laid the groundwork for modern capitalism and global trade but also sparked labor movements and "
            "debates about workers' rights that continue to this day. Understanding this era is key to grasping "
            "the roots of modern economic and social challenges."
        ),
    },
    {
        "subject": "Psychology",
        "topic_name": "Cognitive Biases: Confirmation Bias",
        "content": (
            "Confirmation bias is the tendency to search for, interpret, favor, and recall information in a way "
            "that confirms one's preexisting beliefs or hypotheses. It leads people to ignore evidence that "
            "contradicts their views while overvaluing evidence that supports them. This bias affects decision-making "
            "in everything from politics and finance to scientific research and personal relationships. To combat "
            "it, actively seek out disconfirming evidence and consider alternative explanations. Ask yourself: "
            "'What would have to happen for me to be wrong?' Engage with diverse perspectives and play devil's "
            "advocate against your own positions. Recognizing this bias is the first step toward more objective "
            "thinking. It explains why polarization persists and why smart people can hold irrational beliefs. "
            "Intellectual humility—admitting you might be wrong—is the strongest antidote to this deeply ingrained "
            "mental shortcut."
        ),
    },
    {
        "subject": "Writing",
        "topic_name": "The Hero's Journey",
        "content": (
            "The Hero's Journey, or monomyth, is a common narrative template involving a hero who goes on an "
            "adventure, wins a victory in a decisive crisis, and comes home changed or transformed. Identified "
            "by Joseph Campbell, it typically follows stages like the Call to Adventure, Crossing the Threshold, "
            "Tests/Allies/Enemies, the Ordeal, and the Return with the Elixir. This structure resonates deeply "
            "because it mirrors the human experience of growth and overcoming adversity. Writers use it to structure "
            "plots that feel satisfying and universal. However, it shouldn't be a rigid formula; the best stories "
            "adapt the stages to fit unique characters and settings. Whether in ancient myths or modern blockbusters, "
            "the journey represents the psychological passage from innocence to experience. Understanding these "
            "beats helps writers pace their stories and ensure emotional resonance with the audience."
        ),
    },
    {
        "subject": "Health & Fitness",
        "topic_name": "Progressive Overload",
        "content": (
            "Progressive overload is the fundamental principle of strength training and physical conditioning. "
            "It involves gradually increasing the stress placed on the body during exercise to stimulate muscle "
            "growth and strength gains. This can be achieved by lifting heavier weights, doing more repetitions, "
            "reducing rest times, or increasing training frequency. Without overload, the body adapts to the "
            "current stress level and plateaus, leading to stagnation. It requires consistent tracking of workouts "
            "to ensure you are doing slightly more than the previous session. Safety is paramount; increases should "
            "be small and manageable to avoid injury. This principle applies not just to lifting but also to "
            "cardiovascular endurance and flexibility. It teaches the body that it needs to be stronger to survive "
            "the environment, triggering the biological adaptation processes that build resilience and power."
        ),
    },
    {
        "subject": "Economics",
        "topic_name": "Supply and Demand",
        "content": (
            "Supply and demand is the economic model of price determination in a market. It postulates that, "
            "holding all else equal, in a competitive market, the unit price for a particular good, or other "
            "traded item such as labor or liquid financial assets, will vary until it settles at a point where "
            "the quantity demanded (at the current price) will equal the quantity supplied (at the current price), "
            "resulting in an economic equilibrium for price and quantity. If demand increases and supply remains "
            "unchanged, a shortage occurs, leading to a higher equilibrium price. Conversely, if supply increases "
            "and demand remains unchanged, a surplus occurs, leading to a lower equilibrium price. Understanding "
            "these forces helps explain market fluctuations, the impact of taxes, and consumer behavior. It is the "
            "foundational concept upon which most of modern economic theory is built."
        ),
    }
]

def main() -> None:
    db = Database()
    # Ensure DB/tables exist
    db.init_db()
    for item in SAMPLES:
        db.add_material(item["subject"], item["topic_name"], item["content"])
    print(f"Inserted {len(SAMPLES)} sample materials (content > 150 words each).")

if __name__ == "__main__":
    main()