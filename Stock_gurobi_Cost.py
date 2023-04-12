# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 12:39:35 2023

@author: kaspe
"""


import pandas as pd
import numpy as np 
import gurobipy as gp
from gurobipy import GRB
from Stock_Bestseller_classes import *
from Stock_Bestseller_w47 import *
import itertools
import time
import math


def gurobi_stock_cost(order_id, sku_id, S_k, Warehouses, M_j, N_j, C_km_jk, E_km_jk, q,  D_in_cost,D_in_CO2, D_out, surface_i, weigth_dict,reduction,lim):
    model = gp.Model("stock_allo_Cost")
    model.Params.LogToConsole = 0
    

    y, x, z, F_s, dc, wdc, zwdc = {}, {}, {},{}, {}, {}, {}
    for i in sku_id:
        for j in Warehouses:
            y[i,j] = model.addVar(obj=0, vtype="B", name="y[%s,%s]"%(i,j))
            
    for j in Warehouses:
        for k in order_id:
            #A[k] = model.addVar(obj=0, vtype="C", name="A[%s]"%(k))
            z[j,k] = model.addVar(obj=0, vtype="B", name="z[%s,%s]"%(j,k))
            
            dc[j,k] = D_out[j,k] #C_km_jk*
            wdc[j,k] = model.addVar(obj=0, vtype="C", name="wdc[%s,%s]"%(j,k))
            zwdc[j,k] = model.addVar(obj=0, vtype="C", name="zwdc[%s,%s]"%(j,k))
            F_s[k] =  model.addVar(obj=0, vtype="C", name="F_s[%s]"%(k))
    

    for j in Warehouses: 
        for k in S_k.keys():  
            for i in sku_id:
                x[i,j,k] = model.addVar(obj=0, vtype="B", name="x[%s,%s, %s]"%(i,j,k)) 
    model.update()
    
    I_k, W_k = {}, {}
    for k in S_k.keys():
        I_k[k] = len(S_k[k])
        W_k[k] =  gp.quicksum(z[jj,k] for jj in Warehouses)
        
    
    # all SKUs must be allocated to at least one warehouse
    for i in sku_id:
        model.addConstr(gp.quicksum(y[i,j] for j in Warehouses), ">=", 1, name="Allocate[%s]"%i)
    
    # no warehouse can contain more or less SKUs than it is specified in its capacity
    for j in Warehouses:
         model.addConstr(gp.quicksum(y[i,j] for i in sku_id), "<=", M_j[j], name="Max[%s]"%i)
         
    for j in Warehouses:
        model.addConstr(gp.quicksum(y[i,j] for i in sku_id), ">=", N_j[j], name="Min[%s]"%j)
    
    #SKU required by a given order is shipped from exactly one of the warehouses                                                
    for k, values in S_k.items():  
        for i in values:
            model.addConstr(gp.quicksum(x[i,j,k] for j in Warehouses), "==", 1, name="shipped[%s,%s]"%(i,k))
    
    
    for j in Warehouses: 
        for k, values in S_k.items():  
            model.addConstr(dc[j,k]*gp.quicksum(weigth_dict[i]*x[i,j,k] for i in sku_id), "==", wdc[j,k] , name="wdc[%s,%s]"%(j,k))
            model.addConstr(z[j,k]*wdc[j,k], "==", zwdc[j,k] , name="zwdc[%s,%s]"%(j,k))
            for i in values:
                #that SKUs will be shipped from warehouses where they have been allocated
                model.addConstr(x[i,j,k], "<=", y[i,j], "loc")
                #that there will be a shipment from every warehouse where there is at least one SKU to ship
                model.addConstr(x[i,j,k], "<=", z[j,k], "ship")

    if reduction == 'A1':
        #model.params.NonConvex = -1
        model.params.NonConvex = 2
        ##reduction A_1
        print('Using reduction function:', reduction)
        for k in S_k.keys(): 
            model.addConstr(F_s[k], '==', 1-(I_k[k] - W_k[k])*q, name="reduction[%s]"%(k) )
    if reduction == 'A2': 
        model.params.NonConvex = 2
        ##reduction A_2  
        print('Using reduction function:', reduction)      
        for k in S_k.keys(): 
            model.addConstr(W_k[k]*(1+q-F_s[k]), '==', I_k[k]*q, name="reduction[%s]"%(k) )
            
            
    model.setObjective(gp.quicksum(y[i,j]*D_in_cost[i,j]  for j in Warehouses for i in sku_id )
                      + 
                      gp.quicksum(F_s[k] * gp.quicksum(zwdc[j,k] for j in Warehouses) for k in  S_k.keys()))
    model.update()
    model.__data = x,y,z,F_s,wdc, zwdc
                      
    model.ModelSense = GRB.MINIMIZE   
    model.Params.TimeLimit = 3600
    model.optimize()
    
        
    print("Cost optimal", model.objVal)
    
    W,O,S = intialize(Warehouses, M_j, N_j,S_k,sku_id)
    for p in y:
        if math.isclose(y[p].x, 1): 
            w = W.get_warehouse_based_on_ID(p[1]) 
            w.add_product_to_warehouse(p[0])
            sup =  S.get_product_based_on_ID(p[0])
            sup.in_warehouse.append(p[1])
        
    return W, O, S
    # for pp in z: 
    #     if z[pp].x == 1:
    #         w = W.get_warehouse_based_on_ID(pp[0])
    #         w.sent_order_from_Warehouse(pp[1])
    #         orde = O.get_order_based_on_ID(pp[1])
    #         orde.add_warehouses_used(pp[0])
            
    # w_sents = {}
    # for k,v in W.warehouse_dict.items():
    #     w_sents[k] = len(v.sents_orders)
    
    # for k in O.order_dict.values(): 
    #     all_combo_w = []
    #     singel_items = list(dict.fromkeys(k.purchased_items))
    #     for t in range(0,W.nr_of_warehouses):
    #         for s in itertools.combinations(W.warehouse_list,t+1):
    #             combination_w = [] 
    #             all_products = []
    #             for r in s:
    #                 all_products = all_products + r.holds_products
    #                 combination_w.append(r.ID)
    #             if len(singel_items) == len(list(set(singel_items) & set(all_products))): 
    #                all_combo_w.append(combination_w)
    #     k.warehouses_combinations =  all_combo_w
        
    # splits  = dict.fromkeys(range(W.nr_of_warehouses), 0)
    # for k in O.order_dict.values(): 
    #     splits[len(k.warehouses_used)-1] += 1      
        
    
    # F_sr = {}
    # for k  in O.order_dict.values(): 
    #      W_kr =  len(k.warehouses_used)
    #      I_kr = len(k.purchased_items)
    #      if reduction == 'A1':
    #              F_sr[k.ID] = 1-(I_kr - W_kr)*q
    #      #model.params.NonConvex = -1
    #      if reduction == 'A2': 
    #              F_sr[k.ID] = 1 - (I_kr/W_kr - 1)*q
            
            
            
    # print("Cost optimal", model.objVal)
    # total_cost = sum([y[i,j].x *D_in_cost[i,j] for i in sku_id  for j in Warehouses]) + sum([F_sr[k] * C_km_jk * sum([z[j,k].x * D_out[j,k] * (sum([weigth_dict[i] * x[i,j,k].x for i in sku_id])) for j in Warehouses]) for k in S_k.keys()])
    # total_CO2  = sum([y[i,j].x *D_in_CO2[i,j]  for i in sku_id  for j in Warehouses]) + sum([F_sr[k] * E_km_jk * sum([z[j,k].x * D_out[j,k] * (sum([weigth_dict[i] * x[i,j,k].x for i in sku_id])) for j in Warehouses]) for k in S_k.keys()])
    # total_pack = sum([sum([x[ii,j,k].x*surface_i[ii] for ii in values]) - F_packing(sum([x[ii,j,k].x for ii in values])) for j in Warehouses for k, values in S_k.items()])
    # print("Cost calculated", total_cost)

    # ship = sum([1 for j in Warehouses for k in   S_k.keys() if z[j,k].x==1])
    # avg_ship = ship/O.nr_of_orders
    # avg_fulfill_option = sum([len(k.warehouses_combinations) for k in O.order_dict.values()])/O.nr_of_orders

    # per_split = (sum(list(splits.values())[1:])/O.nr_of_orders)*100
    # nr_shipment_per_w = {j:sum([1 for k in S_k.keys() if z[j,k].x == 1]) for j in Warehouses}
    
    # result_names = ['#Orders','#Products','#Warehouses','Capacities','#Shipments','Total cost', 'Total CO2','Total Pack','% of order split'] + [f'#Order with {a} splits' for a in splits.keys()] + ['Avg #shipments per order']+ ['Avg fulfillment options per order']+ [f'#Order from W{a}' for a in nr_shipment_per_w.keys()] + ['runtime'] 
    # result_list = [O.nr_of_orders]+[S.nr_of_products]+[W.nr_of_warehouses]+[[A.max_cap for A in W.warehouse_dict.values()]]+[ship]+[round(total_cost,2)]+[round(total_CO2,2)]+[round(total_pack,6)]+[round(per_split,3)] + list(splits.values())+ [round(avg_ship,3)] + [round(avg_fulfill_option,3)] + list(nr_shipment_per_w.values()) + [time.time() - start_time]
    
    # return result_names, result_list