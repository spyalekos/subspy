# Αρχικοποίηση git (αν δεν υπάρχει)
git init
# Προσθήκη αρχείων
git add .
# Commit
git commit -m "SubsPy v1.21 - Εφαρμογή Διαχείρισης Συνδρομών"
# Δημιούργησε πρώτα ένα repository στο github.com με όνομα "subspy"
gh repo create subspy --private --source=. --remote=upstream
# Μετά τρέξε:
git remote add origin https://github.com/spyalekos/subspy.git
git branch -M main
git push -u origin main
