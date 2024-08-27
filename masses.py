import pdb
import time
import csv
import json
import pandas as pd
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
import sys

MAX_NUM_SUB = 10

def postProcessing(combs,target,mod_to_mass,sample,exp):
    clean = []
    for comb in combs:
        comp = ""
        mods = 0
        for (mod, experiment), mass in sorted(mod_to_mass.items()):
            if mass in sample and (exp in experiment or experiment == "All"): 
                cnt = comb[0].count(mass) 
                comp += mod + "[x" + str(cnt) + "]_"
                if experiment == "All" and mod_to_mass[(mod,experiment)] < 5000: mods +=cnt
        comp = comp[:-1]
        clean.append([comp,comb[1],mods])
    return clean   


def genDP(nums,max_sum):
    n = len(nums)
    min_sum = min(sum(x for x in nums if x<0),0)
    offset = -min_sum
    dp_size = max_sum - min_sum + 1

    dp = [False] * dp_size
    subsets = [set() for _ in range(dp_size)]
    dp[offset] = True
    subsets[offset].add(())

    for i in range(1,n+1):
        t0 = time.time()
        new_subst = [set(s) for s in subsets]
        new_dp = dp[:]
        for j in range(dp_size-1, -1,-1):
            if dp[j]:
                updated_sum_idx = j + nums[i-1]
                if 0<= updated_sum_idx < dp_size:
                    new_dp[updated_sum_idx] = True
                    for iters,sub in enumerate(subsets[j]):
                        if iters > MAX_NUM_SUB: break 
                        new_s = (sub + (nums[i-1],))
                        new_subst[updated_sum_idx].add(new_s)                
        dp = new_dp
        subsets = new_subst
    return dp, subsets, offset


def idSubs(dp,subsets,L,R,offset):
    dp_size = len(dp)
    ans = []

    for targ in range(L,R+1):
        targ_idx = targ + offset
        if 0<= targ_idx < dp_size and dp[targ_idx]:
            ans.append([list(subsets[targ_idx]), targ])

    ans = [[list(sub),sum_val] for sublist, sum_val in ans for sub in sublist]
    return ans

def lowerStrip(s):
    return ''.join(c.lower() for c in s if not c.isspace())

def preProcessing(mod_path, masses_path):
    mod_df = pd.read_csv(mod_path)
    if mod_df["Mass"].dtype == "object": mod_df['Mass'] = mod_df['Mass'].str.replace(",", "").astype(int) #Handle commas
    masses_to_mod = {tuple([row['Mass'], row['Experiment']]): row['ShortName'] for _, row in mod_df.iterrows()}

    df = pd.read_csv(masses_path).dropna(axis=1,how='all')
    masses = {}
    for col in df:
        temp = df[col].dropna()
        if temp.dtype == 'object': 
            temp = temp.str.replace(",", "").astype(int) # Handle commas
        elif temp.dtype == "float64":
            temp = temp.astype(int)
        temp_l = temp.values.tolist()
        masses[col] = temp_l
    sample = []
    all_df = mod_df[mod_df['Experiment'] == "All"].reset_index()
    for i, val in enumerate(all_df["To"]):
        for j in range(val):
            sample.append(all_df.at[i,"Mass"])

    exp_to_sample = {}
    for exp in masses:
        aux = []
        key = lowerStrip(exp)
        _max = max(masses[exp])
        for i,val in enumerate(mod_df['Experiment']):
            if key in lowerStrip(val):
                cnt = mod_df.at[i,'To'] 
                for j in range(cnt): 
                    aux.append(mod_df.at[i,"Mass"])
        exp_to_sample[key] = [sample + aux, _max]

    return masses_to_mod, masses, exp_to_sample

def getName(path):
    length = len("modifications.csv")
    strip = path[:-length]
    rev = strip[::-1]
    idx = rev.find("\\")
    name = strip[-idx:-1]
    return name

def genOutPath(name,path):
    idx = path[::-1].find("\\")
    return path[:-idx] + name +"_result.csv"

def main(mod_path, masses_path,eps): 
    t0 = time.time()
    name = getName(mod_path)
    mass_to_mod, masses, exp_to_sample  = preProcessing(mod_path,masses_path)
    mod_to_mass = {tuple([mass_to_mod[key], key[1]]) : key[0] for key in mass_to_mod}
    count = 0
    out = pd.DataFrame(columns=["Experiment", "Masses Observed", "Matched Mass","Num_Mods", "Delta Mass"])
    total = len(masses) 
    for num, exp in enumerate(masses):
        print(f"{num+1} / {total} Calculating combinations for experiment {exp}")
        sub_total = 0 
        key = lowerStrip(exp)
        dp, subst, offset = genDP(exp_to_sample[key][0], exp_to_sample[key][1]+eps) 
        for mass in masses[exp]:
            combinations = idSubs(dp,subst, mass-eps, mass +eps,offset)
            comb = postProcessing(combinations,mass,mod_to_mass,exp_to_sample[key][0],exp) 
            count += 1
            sub_total += len(comb)
            if not comb: 
                out.loc[len(out.index)] = [exp, mass, "No Matches","N/A", "N/A"]
            else:
                for c in comb:
                    out.loc[len(out.index)]= [exp,mass,c[0],c[2],(c[1]-mass)]

    path_out = genOutPath(name,mod_path)
    print(f"Calculated combinations for {count} masses in {time.time()-t0} seconds")
    out.to_csv(path_out, index=False)
    print(f"Wrote matches to {path_out}")

#main()