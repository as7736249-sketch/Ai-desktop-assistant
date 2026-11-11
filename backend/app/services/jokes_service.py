"""
Jokes & Quotes service — offline fallback so the app is fun
even when Ollama is down.
"""
import random

JOKES_EN = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break. Now it won't stop sending me KitKat ads.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I would tell you a UDP joke, but you might not get it.",
    "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "Why did the developer go broke? Because he used up all his cache.",
    "A SQL query walks into a bar, walks up to two tables and asks, 'Can I join you?'",
    "Why do Java developers wear glasses? Because they don't C#.",
]

JOKES_HI = [
    "प्रोग्रामर की पत्नी बोली — दूध लेते आना, अगर अंडे हों तो एक दर्जन लेना। प्रोग्रामर बारह दूध लेकर आया।",
    "अध्यापक: बताओ, कंप्यूटर और आदमी में क्या फर्क है? छात्र: कंप्यूटर सोचता नहीं, लेकिन काम करता है।",
    "डॉक्टर: आपको आराम की जरूरत है। मरीज: लेकिन डॉक्टर साहब, मैं तो प्रोग्रामर हूँ, आराम तो कंप्यूटर को चाहिए।",
]

JOKES_PA = [
    "ਸੰਤਾ: ਬੰਤਾ, ਤੂੰ ਏਨਾ ਸਿਆਣਾ ਕਿਵੇਂ ਹੋ ਗਿਆ? ਬੰਤਾ: ਮੈਂ ਹਰ ਰੋਜ਼ Google ਤੋਂ ਸਵਾਲ ਪੁੱਛਦਾ ਹਾਂ।",
    "ਟੀਚਰ: ਬੰਤੇ, ਦੋ ਅਤੇ ਦੋ ਕਿੰਨੇ? ਬੰਤਾ: ਮੈਡਮ, ਕੈਲਕੁਲੇਟਰ ਦੇਖ ਕੇ ਦੱਸਾਂ?",
]

QUOTES_EN = [
    "The only way to do great work is to love what you do. — Steve Jobs",
    "Innovation distinguishes between a leader and a follower. — Steve Jobs",
    "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
    "Success is not final, failure is not fatal: it is the courage to continue that counts. — Winston Churchill",
    "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
    "Be yourself; everyone else is already taken. — Oscar Wilde",
    "Life is what happens when you're busy making other plans. — John Lennon",
    "You miss 100 percent of the shots you don't take. — Wayne Gretzky",
    "The best time to plant a tree was 20 years ago. The second best time is now.",
    "Whether you think you can or you think you can't, you're right. — Henry Ford",
]

QUOTES_HI = [
    "मन के हारे हार है, मन के जीते जीत।",
    "कोशिश करने वालों की कभी हार नहीं होती।",
    "जो सोचते हो, वो बन जाते हो।",
]

QUOTES_PA = [
    "ਸੱਚ ਬੋਲਣ ਵਾਲਾ ਹੀ ਸੱਚਾ ਰਾਜਾ ਹੁੰਦਾ ਹੈ।",
    "ਮਿਹਨਤ ਦਾ ਫਲ ਹਮੇਸ਼ਾ ਮਿੱਠਾ ਹੁੰਦਾ ਹੈ।",
    "ਹਿੰਮਤ ਨਾ ਹਾਰੋ, ਸਫ਼ਲਤਾ ਜ਼ਰੂਰ ਮਿਲੇਗੀ।",
]


class JokesService:
    def joke(self, lang: str = "en") -> str:
        if lang == "hi":
            return random.choice(JOKES_HI)
        if lang == "pa":
            return random.choice(JOKES_PA)
        return random.choice(JOKES_EN)

    def quote(self, lang: str = "en") -> str:
        if lang == "hi":
            return random.choice(QUOTES_HI)
        if lang == "pa":
            return random.choice(QUOTES_PA)
        return random.choice(QUOTES_EN)


jokes_service = JokesService()
