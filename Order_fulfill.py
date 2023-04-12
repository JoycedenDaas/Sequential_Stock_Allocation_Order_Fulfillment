# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 09:41:53 2023

@author: kaspe
"""
import itertools
import random

def F_packing(x):
       a = x
       b = x
       f = 16*a*b - 14*a
       return f 

def sublists(pro):
    permutations = list(itertools.permutations(pro))
    for per in permutations:
        lst = list(per)
        for doslice in itertools.product([True, False], repeat=len(lst)-1):
            slices = []
            start = 0
            for i, slicehere in enumerate(doslice, 1):              
                if slicehere:
                    slices.append(lst[start:i])
                    start = i
            slices.append(lst[start:])
            yield slices

def unique_sublist(lst):
    out, seen = [], set()
    for subl in lst:
        t = tuple(tuple(i) for i in subl)
        if t not in seen:
            seen.add(t)
            out.append(subl)
    return out
    
def order_fulfill_min_split(O,W,surface_i,D_out,weigth_dict,C_km_jk,E_km_jk,reduction,Q):
    random.seed(78912)
    g = True
    for k in O.order_dict.values(): 
        all_combo_w = []
        singel_items = list(dict.fromkeys(k.purchased_items))
        for t in range(0,W.nr_of_warehouses):
            for s in itertools.combinations(W.warehouse_list,t+1):
                combination_w = [] 
                all_products = []
                for r in s:
                    all_products = all_products + r.holds_products
                    combination_w.append(r.ID)
                    skip_combo = False
                for a in all_combo_w:
                    sub_com = 0 
                    for b in a:
                        if b in combination_w:
                            sub_com += 1 
                    if sub_com == len(a): 
                        skip_combo = True
                if skip_combo == False: 
                    if len(singel_items) == len(list(set(singel_items) & set(all_products))): 
                       all_combo_w.append(combination_w)

        k.warehouses_combinations =  all_combo_w 
        if all(len(i) == len(all_combo_w[0]) for i in all_combo_w) and len(all_combo_w)> 1:  
            min_combo = random.choice(all_combo_w)
        else:
            min_combo = k.warehouses_combinations[0]
        k.min_nr_shipments = len(min_combo)
        k.warehouses_used = min_combo
        
        total_cost = 0
        total_CO2 = 0 
        total_pack = 0
        
        already_send = []
        for wa in k.warehouses_used: 
            dist = D_out[wa,k.ID]
            weight = 0
            surface = 0
            pack_to = 0
            total_cost_sub =0
            total_CO2_sub  =0
            for qq in k.purchased_items:
                if qq not in already_send:
                    if qq in W.get_warehouse_based_on_ID(wa).holds_products:
                        weight += weigth_dict[qq]
                        surface += surface_i[qq]
                        pack_to += 1
                        
                        already_send.append(qq)
            total_cost_sub +=  weight * dist #* C_km_jk
            total_CO2_sub  +=  weight * dist #* E_km_jk
            total_pack += surface - F_packing(pack_to)
        
        W_kr =  len(k.warehouses_used)
        I_kr = len(k.purchased_items)
        if reduction == 'A1':
                F_sr = 1-(I_kr - W_kr)*Q
        #model.params.NonConvex = -1
        if reduction == 'A2': 
                F_sr = 1 - (I_kr/W_kr - 1)*Q
                
        total_cost +=  total_cost_sub *  F_sr
        total_CO2  +=  total_CO2_sub *  F_sr
        
        k.total_order_cost =  total_cost
        k.total_order_CO2  =  total_CO2
        k.total_order_pack =  total_pack
       
        for v in k.warehouses_used:
            W.get_warehouse_based_on_ID(v).sent_order_from_Warehouse(k.ID)
        
    print(f'    is done by Min splits')
    

def order_fulfill_min_cost_co2_pack(O,W,surface_i,D_out,weigth_dict,C_km_jk,E_km_jk,reduction,Q,Dist):
    g = True
    for k in O.order_dict.values(): 

        all_combo_w = []
        singel_items = list(dict.fromkeys(k.purchased_items))
        all_combo_cost = {}
        all_combo_co2 = {}
        all_combo_pack = {}
        all_combo_split = {}
        for t in range(0,W.nr_of_warehouses):
            for s in itertools.combinations(W.warehouse_list,t+1):
                combination_w = [] 
                all_products = []
                for r in s:
                    all_products = all_products + r.holds_products
                    
                    combination_w.append(r.ID)
                    skip_combo = False
                for a in all_combo_w:
                    sub_com = 0 
                    for b in a:
                        if b in combination_w:
                            sub_com += 1 
                    if sub_com == len(a): 
                        skip_combo = True
                not_used_products = set(all_products) ^ set(range(1000))
                if len(singel_items) == len(list(set(singel_items) & set(all_products))): 
                    if skip_combo == False: 
                       all_combo_w.append(combination_w)
                       if len(combination_w) == 1:
                           W_kr = len(combination_w)
                           I_kr = len(k.purchased_items)
                           if reduction == 'A1':
                                    F_sr = 1-(I_kr - W_kr)*Q
                           if reduction == 'A2': 
                                    F_sr = 1 - (I_kr/W_kr - 1)*Q
                           
                           all_combo_cost[str(combination_w)] =  D_out[combination_w[0],k.ID]*sum([weigth_dict[ll] for ll in k.purchased_items])*F_sr #*C_km_jk 
                           all_combo_co2[str(combination_w)] =   D_out[combination_w[0],k.ID]*sum([weigth_dict[ll] for ll in k.purchased_items]) *F_sr #*E_km_jk
                           all_combo_pack[str(combination_w)] =  sum([surface_i[ll] for ll in k.purchased_items]) - F_packing(len(k.purchased_items))
                           all_combo_split[str(combination_w)] = str(k.purchased_items)
                       else:
                 
                           cost_split_dict = {}
                           co2_split_dict = {}
                           pack_split_dict = {}
                           
                           one_split_posible = 0
                           for l in range(len(combination_w)):
                               ware_spit = combination_w[l]
                               in_warehouse = W.warehouse_list[ware_spit].holds_products
                               one_split_posible += len(list(set(k.purchased_items) & set(in_warehouse)))
                           
                           if  one_split_posible == len(k.purchased_items): 
                        
                               total_cost_split = 0
                               total_co2_split = 0
                               total_pack_split = 0
                               split_op = []
                               for l in range(len(combination_w)):
                                   
                                   ware_spit = combination_w[l]
                                   in_warehouse = W.warehouse_list[ware_spit].holds_products
                                   sub_split = list(set(k.purchased_items) & set(in_warehouse))
                                   total_cost_split +=  D_out[ware_spit,k.ID]*sum([weigth_dict[ll] for ll in sub_split]) #*C_km_jk
                                   total_co2_split  +=  D_out[ware_spit,k.ID]*sum([weigth_dict[ll] for ll in sub_split]) #*E_km_jk
                                   total_pack_split += sum([surface_i[ll] for ll in sub_split]) - F_packing(len(sub_split))
                                  
                                   split_op.append(sub_split)
                                   
                                   
                               W_kr = len(combination_w)
                               I_kr = len(k.purchased_items)
                               if reduction == 'A1':
                                          F_sr = 1-(I_kr - W_kr)*Q
                               if reduction == 'A2': 
                                          F_sr = 1 - (I_kr/W_kr - 1)*Q
                                
                               all_combo_cost[str(combination_w)] =  total_cost_split * F_sr
                               all_combo_co2[str(combination_w)]  =   total_co2_split  * F_sr
                               all_combo_pack[str(combination_w)] =  total_pack_split
                               all_combo_split[str(combination_w)] = str(split_op)

                           else: 
                          
                               if len(k.purchased_items) - len(combination_w) >= 0 : 
                        
                                   
                                   
                                   all_posible_order_plits = list(sublists(k.purchased_items))
                             
                                   check_splits_1 = [t for t in all_posible_order_plits if  len(t) == len(combination_w)]
                                   check_splits_2 =  [t for t in check_splits_1 if not [] in t]
                                   check_splits_3 = [[sorted(x) for x in lst] for lst in check_splits_2]
                                   check_splits = unique_sublist(check_splits_3)
                                   
                                   #print('Nr of split options', len(check_splits))
                                   
                                   for split in  check_splits:
                                       total_cost_split = 0
                                       total_co2_split = 0
                                       total_pack_split = 0
                                       split_good = True
                                   
                                       for l in range(len(combination_w)):
                                            sub_split = split[l] 
                                            ware_spit = combination_w[l]
                                            in_warehouse = W.warehouse_list[ware_spit].holds_products
                                            if  len(sub_split) == len(list(set(sub_split) & set(in_warehouse))):
                                                split_good = True
                                                total_cost_split +=  D_out[ware_spit,k.ID]*sum([weigth_dict[ll] for ll in sub_split])#*C_km_jk
                                                total_co2_split  +=  D_out[ware_spit,k.ID]*sum([weigth_dict[ll] for ll in sub_split])#*E_km_jk
                                                total_pack_split += sum([surface_i[ll] for ll in sub_split]) - F_packing(len(sub_split))
                                            else:
                                             
                                                split_good = False
                                                break 
                                      
                                       if split_good == True: 
                                           W_kr = len(combination_w)
                                           I_kr = len(k.purchased_items)
                                           if reduction == 'A1':
                                                     F_sr = 1-(I_kr - W_kr)*Q
                                           if reduction == 'A2': 
                                                     F_sr = 1 - (I_kr/W_kr - 1)*Q
                                           
                                           cost_split_dict[str(split)] =  total_cost_split * F_sr
                                           co2_split_dict[str(split)]  =  total_co2_split  * F_sr
                                           pack_split_dict[str(split)] =  total_pack_split
                                 
                                   #order fulfillment
                                   if len(co2_split_dict) > 0: 
                                       if Dist == 1:
                                           min_split_combo = min(cost_split_dict, key=cost_split_dict.get)
                                       elif Dist == 2:
                                           min_split_combo = min(co2_split_dict, key=co2_split_dict.get)
                                       elif Dist == 3: 
                                           min_split_combo = min(pack_split_dict, key=pack_split_dict.get)
                                     
                                       all_combo_cost[str(combination_w)] =  cost_split_dict[min_split_combo]
                                       all_combo_co2[str(combination_w)]  =  co2_split_dict[min_split_combo]
                                       all_combo_pack[str(combination_w)] =  pack_split_dict[min_split_combo]
                                       all_combo_split[str(combination_w)]=  min_split_combo 
             
        #order fulfillment
        if Dist == 1:
            if not all_combo_cost: print(k.ID, singel_items, all_combo_w, all_combo_cost)
            if all(len(i) == len(list(all_combo_cost.keys())[0]) for i in list(all_combo_cost.keys())) and len(all_combo_cost.values())> 1 and len(set(all_combo_cost.values())) == 1:  
                min_combo = random.choice(list(all_combo_cost.keys()))
            else:
                min_combo = min(all_combo_cost, key=all_combo_cost.get)
        elif Dist == 2:
            #if all(len(i) == len(list(all_combo_co2.keys())[0]) for i in list(all_combo_co2.keys())) and len(all_combo_co2.values())> 1 and len(set(all_combo_co2.values())) == 1:  
            #     min_combo = random.choice(list(all_combo_co2.keys()))
            # else:
                min_combo = min(all_combo_co2, key=all_combo_co2.get)
        elif Dist == 3: 
            if not all_combo_pack: print(k.ID, all_combo_pack)
            if all(len(i) == len(list(all_combo_pack.keys())[0]) for i in list(all_combo_pack.keys())) and len(all_combo_pack.values())> 1 and len(set(all_combo_pack.values())) == 1:  
                min_combo = random.choice(list(all_combo_pack.keys()))
            else:
                min_combo = min(all_combo_pack, key=all_combo_pack.get)
            
        
        min_warehouse_combo = [int(u) for u in min_combo.strip('][').split(', ')]
        
        k.warehouses_combinations =  all_combo_w 
        k.min_nr_shipments =  len(min_combo)
        k.warehouses_used  =  min_warehouse_combo 
        k.total_order_cost =  all_combo_cost[min_combo]
        k.total_order_CO2  =  all_combo_co2[min_combo]
        k.total_order_pack =  all_combo_pack[min_combo]
        k.total_order_split =  all_combo_split[min_combo]
     
        for v in k.warehouses_used:
            W.get_warehouse_based_on_ID(v).sent_order_from_Warehouse(k.ID)

    if Dist == 1: 
        matrix = 'Min weighted distance'
    elif Dist == 2: 
        matrix = 'Min CO2'
    elif Dist == 3: 
        matrix = 'Min Surface'

    print(f'    is done by {matrix}')
