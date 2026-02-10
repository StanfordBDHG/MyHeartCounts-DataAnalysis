# - BiologicalSex - Male/Female  
# - Diabetes - Has diabetes diagnosis  
# - Hypertension - Has hypertension diagnosis 
# - sleep_diagnosis1 - Has sleep disorder diagnosis  
# - work - Employment status

import pandas as pd
import json
import altair as alt
import numpy as np
compute_flag = [2]#0,1,2

if 0 in compute_flag:
    types = {
        'sleep_diagnosis1': 'boolean',
        'atwork': 'ordinal',
        'phys_activity': 'ordinal',
        'sleep_time': 'float',
        'sleep_time1': 'float',
        'vigorous_act': 'ordinal',
        'work': 'boolean',
        'sleep_diagnosis2': 'categorical',
        'happiness': 'float',
        'heart_disease': 'categorical',
        'vascular': 'categorical',
        'feel_worthwhile1': 'ordinal',
        'feel_worthwhile2': 'ordinal',
        'feel_worthwhile3': 'ordinal',
        'feel_worthwhile4': 'ordinal',
        'satisfiedwith_life': 'ordinal',
        'BiologicalSex': 'boolean',
        'WakeUpTime': 'float',
        'GoSleepTime': 'float',
        'HeightCentimeters': 'float',
        'WeightKilograms': 'float',
        'Diabetes': 'boolean',
        'Hypertension': 'boolean',
        'Hdl': 'float',
        'Ldl': 'float',
        'TotalCholesterol': 'float',
        'DiastolicBloodPressure': 'float',
        'SystolicBloodPressure': 'float'
    }

    reload_flag = False
    if reload_flag:
        # Read JSON string from a file
        with open('source_data/labels_enrollment_info.json', 'r') as f:
            df = pd.DataFrame(json.loads(f.read())).T

        with open('source_data/labels_labels.json', 'r') as f:
            dflbls,auxlbls_val,auxlbls_cat = pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
            aux = json.loads(f.read())
            for k,v in aux.items():
                df2 = pd.DataFrame(v).T.explode(column=['timestamps','values'])
                df2 = df2.reset_index().rename(columns={'index':'HealthCode'})
                df2['labels'] = k
                dflbls = pd.concat([dflbls, df2], ignore_index=True)
                # summary
                if types[k] == 'boolean' or types[k] == 'categorical':
                    aux2 = df2.groupby(['HealthCode','values']).aggregate({'timestamps':['count','min','max']} ).reset_index()   
                    aux2.columns = [c.strip('_') for c in aux2.columns.map('_'.join)]
                    aux2['labels'] = k
                    auxlbls_cat = pd.concat([auxlbls_cat, aux2], ignore_index=True)
                elif types[k] == 'float' or types[k] == 'ordinal':
                    df2['values'] = pd.to_numeric(df2['values'], errors='coerce')
                    # add 25% and 75% quantiles
                    aux2 = df2.groupby('HealthCode').aggregate({'timestamps':['count','min','max'],
                                            'values':['mean','median','max','min',lambda x: x.quantile(0.25),lambda x: x.quantile(0.75)]}).reset_index()
                    aux2.columns = [c.strip('_') for c in aux2.columns.map('_'.join)]
                
                    aux2['labels'] = k
                    auxlbls_val = pd.concat([auxlbls_val, aux2], ignore_index=True)

        auxlbls_cat.to_csv('temp/cat.csv',index=False)
        auxlbls_val.to_csv('temp/val.csv',index=False)
    else: 
        auxlbls_cat = pd.read_csv('temp/cat.csv')
        auxlbls_val = pd.read_csv('temp/val.csv')

    # Analyse values first

    auxlbls_val.loc[:,[ 'values_mean', 'values_median', 'values_max', 'values_min',
        'values_<lambda_0>', 'values_<lambda_1>','labels']].groupby('labels').mean()

    #                         values_mean  values_median  values_max  values_min  values_25%  values_75%
    # labels                                                                                                          
    # DiastolicBloodPressure    76.389566      76.399505   77.817208   74.971691          75.753715          77.011551
    # GoSleepTime                     NaN            NaN         NaN         NaN                NaN                NaN
    # Hdl                        2.846491       2.846858    2.942923    2.750366           2.805061           2.887792
    # HeightCentimeters        169.179319     169.376857  170.278945  167.697655         168.677256         169.835897
    # Ldl                        5.763295       5.762563    5.928583    5.595296           5.689500           5.837949
    # SystolicBloodPressure    120.260620     120.208608  122.335861  118.346302         119.365926         121.088964
    # TotalCholesterol           9.604654       9.603673    9.805658    9.400143           9.519232           9.691595
    # WakeUpTime                      NaN            NaN         NaN         NaN                NaN                NaN
    # WeightKilograms           77.157179      77.285785   78.417444   75.673144          76.559442          77.844495
    # atwork                     1.291564       1.290765    1.303216    1.281147           1.285916           1.296667
    # feel_worthwhile1           7.333688       7.340972    7.644852    7.001277           7.183704           7.490637
    # feel_worthwhile2           7.054989       7.065165    7.403626    6.680981           6.885993           7.232285
    # feel_worthwhile3           4.579277       4.564755    5.169351    4.027074           4.298836           4.847206
    # feel_worthwhile4           2.597362       2.579999    3.042800    2.199809           2.388738           2.788760
    # happiness                  7.221016       7.288013    7.961086    6.181360           6.942890           7.564917
    # phys_activity              3.026438       3.025707    3.096056    2.956731           2.993261           3.059779
    # satisfiedwith_life         7.094927       7.105111    7.402382    6.762392           6.945989           7.252307
    # sleep_time                 7.814135       7.813702    7.862418    7.768029           7.792652           7.835219
    # sleep_time1                7.062555       7.060119    7.125603    7.004373           7.033892           7.089311
    # vigorous_act              73.407834      72.915853   78.833447   69.044003          70.965898          75.419630

    auxlbls_val.loc[:,[ 'labels','timestamps_count']].groupby('labels').agg(['mean','median','max'])

    #   timestamps_count            
    #                                    mean median  max
    # labels                                             
    # DiastolicBloodPressure         2.393995    1.0  623
    # GoSleepTime                    1.869028    2.0  280
    # Hdl                            2.360074    1.0  624
    # HeightCentimeters              1.870464    2.0  280
    # Ldl                            2.243389    1.0  623
    # SystolicBloodPressure          2.386979    1.0  624
    # TotalCholesterol               2.396498    1.0  624
    # WakeUpTime                     1.869884    2.0  280
    # WeightKilograms                1.870464    2.0  280
    # atwork                         1.215993    1.0   29
    # feel_worthwhile1               2.035947    2.0  116
    # feel_worthwhile2               2.036036    2.0  116
    # feel_worthwhile3               2.035324    2.0  116
    # feel_worthwhile4               2.032847    2.0  116
    # happiness                     10.050204    4.0  137
    # phys_activity                  1.271606    1.0   56
    # satisfiedwith_life             2.037136    2.0  116
    # sleep_time                     1.269979    1.0   56
    # sleep_time1                    1.269803    1.0   56
    # vigorous_act                   1.267454    1.0   56

    # now get the labels one by one

    # get the numeric values first
    auxlbls_val.query('labels in ("Hdl","Ldl","TotalCholesterol","WeightKilograms","sleep_time","vigorous_act")').loc[:,['HealthCode','labels','values_mean', 'values_median', 'values_max', 'values_min']].to_csv('temp/numeric_values.csv',index=False)

    # blood pressure categories

    dia = dflbls.query('labels == "DiastolicBloodPressure"').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).loc[:,['HealthCode','values']]
    dia['values'] = dia['values'].astype(float)

    sys = dflbls.query('labels == "SystolicBloodPressure"').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).loc[:,['HealthCode','values']]
    sys['values'] = sys['values'].astype(float)

    sys_dia = pd.merge(sys, dia, on='HealthCode', suffixes=('_systolic', '_diastolic'))
    # identify the flips
    idx = sys_dia['values_diastolic'] > sys_dia['values_systolic']
    sys_temp = sys_dia.loc[idx,'values_systolic'].copy()
    dia_temp = sys_dia.loc[idx,'values_diastolic'].copy()
    sys_dia.loc[idx,'values_systolic'] = dia_temp
    sys_dia.loc[idx,'values_diastolic'] = sys_temp
    del sys_temp, dia_temp
    # now get into categories
    def categorize_bp(row):
        systolic = row['values_systolic']
        diastolic = row['values_diastolic']
        if systolic < 120 and diastolic < 80:
            return "Normal"
        elif 120 <= systolic < 130 and diastolic < 80:
            return "Elevated"
        elif (130 <= systolic < 140) or (80 <= diastolic < 90):
            return "Hypertension_Stage_1"
        elif (140 <= systolic) or (90 <= diastolic):
            return "Hypertension_Stage_2"
        elif systolic > 180 or diastolic > 120:
            return "Hypertensive_Crisis"
        else:
            return "Uncategorized"
    sys_dia['category'] = sys_dia.apply(categorize_bp, axis=1)
    sys_dia.to_csv('temp/blood_pressure_categories.csv',index=False)

    # BMI 
    height = dflbls.query('labels == "HeightCentimeters"').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).loc[:,['HealthCode','values']]
    height['values'] = height['values'].astype(float) / 100  # convert to meters    
    weight = dflbls.query('labels == "WeightKilograms"').groupby('HealthCode')['values'].max().reset_index()
    weight['values'] = weight['values'].astype(float)
    bmi = pd.merge(weight, height, on='HealthCode', suffixes=('_weight', '_height'))
    bmi['BMI'] = bmi['values_weight'] / (bmi['values_height'] ** 2)
    bmi['category'] = pd.cut(bmi['BMI'], 
                            bins=[0, 19.9, 24.9, 29.9, 39.9, np.inf], 
                            labels=['Underweight', 'Normal weight', 'Overweight', 'Obesity','Morbid Obesity'])
    bmi = bmi.query('values_height>=1.4 and values_height <=2.1 and values_weight >=40')
    bmi.to_csv('temp/bmi_categories.csv',index=False)

    # sleep_time
    sleep_time = dflbls.query('labels == "sleep_time"').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).loc[:,['HealthCode','values']]
    sleep_time['values'] = sleep_time['values'].astype(float)
    sleep_time['category'] = pd.cut(sleep_time['values'], 
                                        bins=[0, 6, 7, 9, np.inf], 
                                        labels=['Insufficient', 'Short', 'Normal', 'Too Long'])
    sleep_time.query('values<=12').to_csv('temp/sleep_time_categories.csv',index=False)

    # WakeUpTime - these might be all wrong
    wake_time = dflbls.query('labels == "WakeUpTime"').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).loc[:,['HealthCode','values']]
    wake_time['local_time'] = pd.to_datetime(wake_time['values']).dt.tz_localize(None)
    wake_time['hour'] = pd.to_datetime(wake_time['local_time']).dt.hour + (wake_time['local_time'].dt.minute / 60)
    wake_time['category'] = pd.cut(wake_time['hour'], 
                                            bins=[0, 5, 7, 9, 24], 
                                            labels=['Early Riser', 'Normal Riser', 'Late Riser', 'Very Late Riser'])
    wake_time.to_csv('temp/wake_time_categories.csv',index=False)

    # GoSleepTime
    go_sleep_time = dflbls.query('labels == "GoSleepTime"').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).loc[:,['HealthCode','values']]
    go_sleep_time['local_time'] = pd.to_datetime(go_sleep_time['values']).dt.tz_localize(None)
    go_sleep_time['hour'] = pd.to_datetime(go_sleep_time['local_time']).dt.hour+ (go_sleep_time['local_time'].dt.minute / 60)
    go_sleep_time['category'] = pd.cut(go_sleep_time['hour'], 
                                                    bins=[0, 1, 7,19,21, 23, 24], ordered=False,
                                                    labels=['Late Sleeper','Very Late Sleeper','Shift Worker','Early Sleeper', 'Normal Sleeper', 'Late Sleeper'])
    go_sleep_time.to_csv('temp/go_sleep_time_categories.csv',index=False)

    # psychological factors
    #                       count      mean       std  min  25%  50%  75%   max
    # labels                                                                   
    # feel_worthwhile1    62188.0  7.488197  2.038789  0.0  7.0  8.0  9.0  10.0
    # feel_worthwhile2    62207.0  7.209880  2.076224  0.0  6.0  8.0  9.0  10.0
    # feel_worthwhile3    62171.0  4.292628  2.788223  0.0  2.0  4.0  7.0  10.0
    # feel_worthwhile4    61888.0  2.433412  2.644067  0.0  0.0  1.0  4.0  10.0
    # satisfiedwith_life  62261.0  7.270796  1.988985  0.0  6.0  8.0  9.0  10.0

    cuts = {'feel_worthwhile1':[0,4,6,8,10.1],
            'feel_worthwhile2':[0,4,6,8,10.1],
            'feel_worthwhile3':[0,4,6,8,10.1],
            'feel_worthwhile4':[0,1,3,5,10.1],
            'satisfiedwith_life':[0,4,6,8,10.1]}
    dfpsych_all = pd.DataFrame()
    for var,cut in cuts.items():
        dfpsych = dflbls.query('labels == @var').sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).copy()
        dfpsych['values'] = pd.to_numeric(dfpsych['values'], errors='coerce')
        # dfcut with the above thresholds
        dfpsych['category'] = pd.cut(dfpsych['values'], bins=cut, labels=['Low','Medium','High','Very High'])
        dfpsych_all = pd.concat([dfpsych_all, dfpsych], ignore_index=True)
    dfpsych_all.to_csv('temp/psychological_factors_categories.csv',index=False)

    # happiness                  7.221016       7.288013    7.961086    6.181360           6.942890           7.564917
    dfhappiness = dflbls.query('labels == "happiness"').copy()
    dfhappiness['values'] = pd.to_numeric(dfhappiness['values'], errors='coerce')
    # longitudinal happiness
    idx = dfhappiness.groupby('HealthCode')['values'].count()
    idx = idx[idx>=3].index
    dfhappiness_long = dfhappiness[dfhappiness['HealthCode'].isin(idx)].copy()
    # plot it - sample 20 participants
    sample_ids = dfhappiness_long['HealthCode'].sample(n=10, random_state=42).values
    dfhappiness_long2 = dfhappiness_long[dfhappiness_long['HealthCode'].isin(sample_ids)].copy() 
    alt.Chart(dfhappiness_long2).mark_circle().encode(
        x='timestamps:T',
        y='values:Q',
        color='HealthCode:N',
        tooltip=['HealthCode:N','timestamps:T','values:Q']
    ).properties(
        title='Longitudinal Happiness Scores'
    ).save('figures/happiness_longitudinal.html')
    dfhappiness_long.to_csv('temp/happiness_longitudinal.csv',index=False)

    # happiness static values - categories
    dfhappiness_static = dfhappiness.sort_values(by='timestamps',ascending=False).drop_duplicates(subset=['HealthCode']).copy()
    dfhappiness_static['values'] = pd.to_numeric(dfhappiness_static['values'], errors='coerce')
    dfhappiness_static['category'] = pd.cut(dfhappiness_static['values'], 
                                            bins=[0, 4, 6, 8, 10], 
                                            labels=['Low','Medium','High','Very High'])
    dfhappiness_static.to_csv('temp/happiness_static_categories.csv',index=False)

    # phys_activity              3.026438       3.025707    3.096056    2.956731           2.993261           3.059779
    # vigorous_act             73.407834      72.915853   78.833447   69.044003          70.965898          75.419630
    dfactivity = dflbls.query('labels in ["phys_activity"]').sort_values(by='timestamps',ascending=False).copy()
    dfactivity['values'] = pd.to_numeric(dfactivity['values'], errors='coerce')
    dfvig = dflbls.query('labels in ["vigorous_act"]').sort_values(by='timestamps',ascending=False).copy()
    dfvig['values'] = pd.to_numeric(dfvig['values'], errors='coerce')
    # merge
    # dfact = pd.merge(dfactivity.loc[:,['HealthCode','values']], 
    #                  dfvig.loc[:,['HealthCode','values']],
    #                    on=['HealthCode'], suffixes=('_phys','_vig'))
    dfvig['labels'] = pd.cut(dfvig['values'], 
                                    bins=[-1, 150, 300, 420, np.inf], 
                                    labels=['Below recommendation','Good','High volume','Athlete training'])
    dfactivity['labels'] = pd.cut(dfactivity['values'], 
                                    bins=[-1, 2, 4.1, np.inf], 
                                    labels=['Infrequent','Moderate','Frequent'])

    # sample_ids = dfact['HealthCode'].sample(n=100, random_state=42).values
    # dfact2 = dfact[dfact['HealthCode'].isin(sample_ids)].copy() 

    # alt.Chart(dfact2).mark_circle().encode(x='values_vig:Q',
    #                                     y='values_phys:N',
    #                                     detail='HealthCode:N',
    #                                     tooltip=['HealthCode:N','vig_category:N','phys_category:N']).save('figures/physical_activity_scatter.html')
    # dfact.to_csv('temp/physical_activity_categories.csv',index=False)
    dfvig.to_csv('temp/vigorous_categories.csv',index=False)
    dfactivity.to_csv('temp/physical_activity_categories.csv',index=False)

    auxlbls_cat.groupby('labels').aggregate({'timestamps_count':'sum',
                                            'HealthCode':'nunique'}).sort_values('HealthCode',ascending=False)
    #                   timestamps_count  HealthCode
    # labels                                         
    # heart_disease                42640        29957
    # vascular                     40090        29954
    # sleep_diagnosis2               966          348

    # current labels - binary 
    # BiologicalSex                45838        25217
    # Diabetes                     24384        10209
    # Hypertension                 24385        10209
    # sleep_diagnosis1             56541        44498
    # work                         56471        44430

    auxlbls_val.groupby('labels').aggregate({'timestamps_count':'sum',
                                            'HealthCode':'nunique'}).sort_values('HealthCode',ascending=False)

    # Labels for regression
    #                         timestamps_count  HealthCode
    # labels                                               
    # phys_activity                      56514        44443
    # sleep_time1                        56331        44362
    # sleep_time                         56335        44359
    # vigorous_act                       53863        42497
    # atwork                             45072        37066
    # satisfiedwith_life                 62261        30563
    # feel_worthwhile2                   62207        30553
    # feel_worthwhile3                   62171        30546
    # feel_worthwhile1                   62188        30545
    # feel_worthwhile4                   61888        30444
    # WeightKilograms                    47579        25437
    # HeightCentimeters                  47579        25437
    # GoSleepTime                        47378        25349
    # WakeUpTime                         47237        25262
    # SystolicBloodPressure              24235        10153
    # TotalCholesterol                   23814         9937
    # DiastolicBloodPressure             23679         9891
    # Hdl                                21682         9187
    # Ldl                                15356         6845
    # happiness                          41839         4163

    # plot distribution of one of the labels
    auxlbls_cat = pd.read_csv('temp/cat.csv')
    # auxlbls_cat = auxlbls_cat.melt(id_vars=['HealthCode','labels',
    #                                         'values','timestamps_count'], 
    #                                         value_vars=['timestamps_min', 'timestamps_max'], 
    #                                         var_name='timestamp', value_name='timestamp_values')


    heart_disease_map = {
        "1": "Heart Attack/Myocardial Infarction",
        "2": "Heart Bypass Surgery",
        "3": "Coronary Blockage/Stenosis",
        "4": "Coronary Stent/Angioplasty",
        "5": "Angina (heart chest pains)",
        "6": "High Coronary Calcium Score",
        "7": "Heart Failure or CHF",
        "8": "Atrial fibrillation (Afib)",
        "9": "Congenital Heart",
        "10": "None of the above",
        "11": "Pulmonary Hypertension"
    }

    vascular_map = {
        "1": "Stroke",
        "2": "Transient Ischemic Attack (TIA)",
        "3": "Carotid Artery Blockage/Stenosis",
        "4": "Carotid Artery Surgery or Stent",
        "5": "Peripheral Vascular Disease (Blockage/Stenosis, Surgery, or Stent)",
        "6": "Abdominal Aortic Aneurysm",
        "7": "None of the above",
        "8": "Pulmonary Arterial Hypertension"
    }

    # map vascular diseases
    def map_diseases(labels,mapping):
        a = auxlbls_cat.query(f'labels=="{labels}"')
        a['values'] = a['values'].astype(float).astype(int).astype(str)
        a['values'] = a['values'].map(mapping)
        auxlbls_cat.loc[a.index,'values'] = a['values']
        return auxlbls_cat
    auxlbls_cat = map_diseases('vascular',vascular_map)
    auxlbls_cat = map_diseases('heart_disease',heart_disease_map)

    cerebrovascular = [
        "Stroke",
        "Transient Ischemic Attack (TIA)",
        "Carotid Artery Blockage/Stenosis",
        "Carotid Artery Surgery or Stent"
    ]

    peripheral_systemic = [
        "Abdominal Aortic Aneurysm",
        "Peripheral Vascular Disease (Blockage/Stenosis, Surgery, or Stent)"
    ]

    pulmonary = [
        "Pulmonary Arterial Hypertension",
        "Pulmonary Hypertension"
    ]

    CAD_cols = ['Angina (heart chest pains)', 
                'Coronary Blockage/Stenosis',
                'Coronary Stent/Angioplasty', 
                'Heart Attack/Myocardial Infarction',
                'Heart Bypass Surgery',
                'High Coronary Calcium Score']

    def map_systems(systems, system_name):
        idx = auxlbls_cat['values'].isin(systems)
        auxlbls_cat.loc[idx,'values'] = system_name
        return auxlbls_cat

    auxlbls_cat = map_systems(cerebrovascular, 'Cerebrovascular Disease')
    auxlbls_cat = map_systems(peripheral_systemic, 'Peripheral/Systemic Vascular Disease')
    auxlbls_cat = map_systems(pulmonary, 'PH')
    auxlbls_cat = map_systems(CAD_cols, 'CAD')
    # unify labels
    auxlbls_cat.loc[auxlbls_cat['labels'].isin(['vascular','heart_disease']),'labels'] = 'cardiovascular_disease'

    cat_summ = auxlbls_cat.query('labels!="sleep_diagnosis2"').groupby(['labels','values'])['HealthCode'].nunique().reset_index().rename(columns={'HealthCode':'n_participants'})
    # compute percentage
    cat_tot = cat_summ.groupby('labels')['n_participants'].transform('sum')
    cat_summ['percentage'] = cat_summ['n_participants'] / cat_tot * 100
    cat_summ.to_csv('temp/cat_summary.csv',index=False)
    auxlbls_cat.query('labels!="sleep_diagnosis2"').to_csv('temp/cat_final.csv',index=False)

    # plot the distributions
    for labels in auxlbls_cat['labels'].unique():
        aux = auxlbls_cat[auxlbls_cat['labels']==labels]
        aux['timestamps_count'] = aux['timestamps_count'].astype(int)
        aux['timestamps_count_bins'] = pd.cut(aux['timestamps_count'],bins=[0,1,2,5,10,np.inf], labels=['1','2','3-5','6-10','10+'])
        chart = alt.Chart(aux).mark_bar().encode(
            x=alt.X('timestamps_count_bins:O').sort(['1','2','3-5','6-10','10+']),
            y='count()',
            color='values:N',
            tooltip=['timestamps_count_bins','values:N','count()']
        ).properties(
            title=f'Distribution of {labels}'
        ).facet(column='values:N').save(f'figures/{labels}_distribution.html')


# merge labels
if 1 in compute_flag:
    files = ['sleep_time_categories.csv', 
    'blood_pressure_categories.csv',
        'wake_time_categories.csv', 
            'go_sleep_time_categories.csv', 
            'bmi_categories.csv']

    # merge all labels - categories
    df_final = pd.DataFrame()
    for file in files:
        df = pd.read_csv('temp/'+file).loc[:,['HealthCode','category']]
        df['label_type'] = file.replace('_categories.csv','')
        df_final = pd.concat([df_final, df], axis=0, ignore_index=True)

    # handle exceptions
    # file = 'physical_activity_categories.csv'
    # df = pd.read_csv(f'temp/{file}').loc[:,['HealthCode','phys_category','vig_category']]
    # df['label_type'] = file.replace('_categories.csv','')
    # df_final = pd.concat([df_final, df], axis=0, ignore_index=True)
    file = 'psychological_factors_categories.csv'
    df = pd.read_csv(f'temp/{file}').loc[:,['HealthCode','category','labels']].rename(columns={'labels':'label_type'})
    df_final = pd.concat([df_final, df], axis=0, ignore_index=True)

    df = pd.read_csv('temp/cat_final.csv').rename(columns={'labels':'label_type','values':'category'}).loc[:,['HealthCode','category','label_type']]
    df_final = pd.concat([df_final, df], axis=0, ignore_index=True)
    df_final.to_csv('temp/merged_categorical_labels.csv', index=False)
    aux = df_final.groupby(['label_type','category'])['HealthCode'].nunique().reset_index()
    auxt = aux.groupby(['label_type'])['HealthCode'].sum()
    aux = aux.merge(auxt,on='label_type',suffixes=('','_total'), how='left',)
    aux['proportion'] = aux['HealthCode']/aux['HealthCode_total']*100
    aux.drop(columns=['HealthCode_total'], inplace=True)
    aux.to_csv('temp/label_counts.csv',index=False)

    # handle numeric labels
    files = ['numeric_values.csv', 
            'bmi_categories.csv']
    df = pd.read_csv('temp/'+files[0])
    df2 = pd.read_csv('temp/'+files[1])
    df2.rename(columns={'BMI':'values'}, inplace=True)
    df2['labels'] = 'BMI'
    df.rename(columns={'values_median':'values'}, inplace=True)
    df_final = pd.concat([df.loc[:,['HealthCode','values','labels']],
                        df2.loc[:,['HealthCode','values','labels']]], axis=0, ignore_index=True)
    df_final.to_csv('temp/merged_numeric_labels.csv', index=False)


    df_final.groupby(['labels']).agg({'HealthCode':'nunique',
                                    'values':['mean','median','std','min','max']}).to_csv('temp/value_counts.csv',index=True)


if 2 in compute_flag:
    import json

    # numeric labels - 'temp/merged_numeric_labels.csv'
    dfn = pd.read_csv('temp/merged_numeric_labels.csv')

    # categorical labels - 'temp/merged_categorical_labels.csv'
    dfc = pd.read_csv('temp/merged_categorical_labels.csv')
    dfc.rename(columns={'category':'values','label_type':'labels'},inplace=True)

    # longitudinal labels - 'temp/longitudinal_labels.csv'
    dfl = pd.read_csv('temp/happiness_longitudinal.csv')

    df = pd.concat([dfn, dfc,dfl], axis=0, ignore_index=True)
    df['timestamps'] = df['timestamps'].fillna('')

    grouped = df.groupby(['labels', 'HealthCode']).agg({
        'values': list,
        'timestamps': list
    })

    # 3. Transform to nested dictionary structure
    final_dict = {}

    # Iterate through the multi-index groups
    for (label, health_code), row in grouped.iterrows():
        if label not in final_dict:
            final_dict[label] = {}
        
        final_dict[label][health_code] = {
            "timestamps": row['timestamps'],
            "values": row['values']
        }

    # 4. Save to local file
    file_name = "source_data/last_labels.json"
    with open(file_name, "w") as f:
        json.dump(final_dict, f, indent=2)

    print(f"Saved to {file_name}")


