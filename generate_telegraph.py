"""
Generate Telegraph page HTML for all badges
This creates HTML content that you can copy to telegra.ph
"""

# Badge definitions (copied directly to avoid import issues)
BADGE_DEFINITIONS = {
    'first_test': {'name': '🎯 Birinchi Test', 'description': 'Birinchi testni tugatdingiz', 'emoji': '🎯'},
    'first_perfect': {'name': '💯 Mukammal', 'description': 'Birinchi 100% natija', 'emoji': '💯'},
    'bronze_solver': {'name': '🥉 Bronza O\'quvchi', 'description': '50 ta savolga javob berdingiz', 'emoji': '🥉'},
    'silver_solver': {'name': '🥈 Kumush O\'quvchi', 'description': '200 ta savolga javob berdingiz', 'emoji': '🥈'},
    'gold_solver': {'name': '🥇 Oltin O\'quvchi', 'description': '500 ta savolga javob berdingiz', 'emoji': '🥇'},
    'diamond_solver': {'name': '💎 Olmos O\'quvchi', 'description': '1000 ta savolga javob berdingiz', 'emoji': '💎'},
    'bronze_tester': {'name': '🎓 Bronza Sinov', 'description': '10 ta test tugatdingiz', 'emoji': '🎓'},
    'silver_tester': {'name': '🏅 Kumush Sinov', 'description': '50 ta test tugatdingiz', 'emoji': '🏅'},
    'gold_tester': {'name': '🏆 Oltin Sinov', 'description': '100 ta test tugatdingiz', 'emoji': '🏆'},
    'accurate': {'name': '🎯 Aniq', 'description': '80% aniqlik (50+ savol)', 'emoji': '🎯'},
    'sharpshooter': {'name': '🏹 Nishonchi', 'description': '90% aniqlik (100+ savol)', 'emoji': '🏹'},
    'sniper': {'name': '🎖️ Snayper', 'description': '95% aniqlik (200+ savol)', 'emoji': '🎖️'},
    'week_warrior': {'name': '📅 Haftalik Jangchi', 'description': '7 kun ketma-ket test topdingiz', 'emoji': '📅'},
    'month_master': {'name': '📆 Oylik Usta', 'description': '30 kun ketma-ket test topdingiz', 'emoji': '📆'},
    'exam_passer': {'name': '🎓 Imtihonchi', 'description': 'Imtihon rejimini o\'tdingiz', 'emoji': '🎓'},
    'exam_ace': {'name': '⭐ Imtihon Ustasi', 'description': '5 ta imtihonni o\'tdingiz', 'emoji': '⭐'},
    'speed_demon': {'name': '⚡ Tez', 'description': '10 ta testni 1 kunda tugatdingiz', 'emoji': '⚡'},
    'night_owl': {'name': '🦉 Tungi Qush', 'description': 'Tunda (00:00-06:00) test topdingiz', 'emoji': '🦉'},
    'early_bird': {'name': '🐦 Erta Qush', 'description': 'Erta (05:00-07:00) test topdingiz', 'emoji': '🐦'},
    'comeback': {'name': '🔥 Qaytish', 'description': 'Barcha xato javoblarni to\'g\'riladingiz', 'emoji': '🔥'},
    'legend': {'name': '👑 Afsonaviy', 'description': 'TOP-3 reytingda', 'emoji': '👑'},
    'perfectionist': {'name': '💎 Perfektsionist', 'description': '10 ta mukammal test (100%)', 'emoji': '💎'}
}

def generate_telegraph_html():
    """Generate HTML for Telegraph page showing all badges"""
    
    html = """
<h3>🏅 PDD Test Bot - Barcha Yutuq Nishonlari</h3>

<p><em>Barcha nishonlarni qo'lga kiriting va o'z professional darajangizni ko'rsating!</em></p>

<hr>

<h4>🌟 BOSHLANG'ICH NISHONLAR</h4>
"""
    
    # Beginner badges
    beginner_badges = ['first_test', 'first_perfect']
    for badge_id in beginner_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += "<hr>\n\n<h4>📚 SAVOLLAR NISHONLARI</h4>\n"
    
    # Question badges
    question_badges = ['bronze_solver', 'silver_solver', 'gold_solver', 'diamond_solver']
    for badge_id in question_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += "<hr>\n\n<h4>📝 TEST NISHONLARI</h4>\n"
    
    # Test badges
    test_badges = ['bronze_tester', 'silver_tester', 'gold_tester']
    for badge_id in test_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += "<hr>\n\n<h4>🎯 ANIQLIK NISHONLARI</h4>\n"
    
    # Accuracy badges
    accuracy_badges = ['accurate', 'sharpshooter', 'sniper']
    for badge_id in accuracy_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += "<hr>\n\n<h4>🎓 IMTIHON NISHONLARI</h4>\n"
    
    # Exam badges
    exam_badges = ['exam_passer', 'exam_ace']
    for badge_id in exam_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += "<hr>\n\n<h4>⚡ MAXSUS NISHONLAR</h4>\n"
    
    # Special badges
    special_badges = ['speed_demon', 'night_owl', 'early_bird', 'comeback', 'week_warrior', 'month_master']
    for badge_id in special_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += "<hr>\n\n<h4>👑 AFSONAVIY NISHONLAR</h4>\n"
    
    # Legendary badges
    legendary_badges = ['legend', 'perfectionist']
    for badge_id in legendary_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge = BADGE_DEFINITIONS[badge_id]
            html += f"""
<p><strong>{badge['emoji']} {badge['name']}</strong><br>
<em>{badge['description']}</em></p>
"""
    
    html += """
<hr>

<h4>📊 STATISTIKA</h4>
<p>Jami nishonlar: <strong>{}</strong></p>
<p>Kategoriyalar: <strong>6</strong></p>

<hr>

<p><em>🚗 PDD Test Bot bilan professional haydovchi bo'ling!</em></p>

<p><strong>Bot:</strong> @pdd_test_uz_bot (namuna nomi)</p>
""".format(len(BADGE_DEFINITIONS))
    
    return html

if __name__ == "__main__":
    html_content = generate_telegraph_html()
    
    # Save to file
    with open('/media/agex/Agex-Store/ppd/ppdv5/', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Telegraph HTML generated!")
    print("\n📝 Instructions:")
    print("1. Go to https://telegra.ph/")
    print("2. Click 'Create Page'")
    print("3. Copy content from telegraph_badges.html")
    print("4. Paste into Telegraph editor")
    print("5. Publish and copy the URL")
    print("6. Update TELEGRAPH_ALL_BADGES_URL in handlers/badges.py")
    print(f"\n📄 HTML file saved to: /home/claude/telegraph_badges.html")
    print("\n" + "="*50)
    print("\nPreview of HTML content:")
    print("="*50)
    print(html_content[:500] + "...")
