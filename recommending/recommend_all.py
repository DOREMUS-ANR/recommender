from recommending import recommend

with open("all_expressions.txt") as all_exp_file:
    all_exp = all_exp_file.read()
    # remove last empty line
    if not all_exp[-1]:
        all_exp = all_exp[:-1]

for e in all_exp.split('\n'):
    print('**** RECOMMENDING %s ****' % e)
    recommend.main({'expression': e})
