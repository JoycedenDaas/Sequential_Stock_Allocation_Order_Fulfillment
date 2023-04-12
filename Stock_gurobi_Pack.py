# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 15:24:41 2023

@author: kaspe
"""



import pandas as pd
import numpy as np 
import gurobipy as gp
from gurobipy import GRB
from Stock_Bestseller_classes import *
from Stock_Bestseller_w47 import *
import itertools
from itertools import chain
import time
import math



def gurobi_stock_pack(order_id, sku_id, S_k, Warehouses, M_j, N_j, C_km_jk, E_km_jk, Q,  D_in_cost,D_in_CO2, D_out, surface_i, weigth_dict,reduction, lim):
    model = gp.Model("stock_allo_pack")
    model.Params.LogToConsole = 0
    
    y, x, z = {}, {}, {},  
    for i in sku_id:
        for j in Warehouses:
            y[i,j] = model.addVar(obj=0, vtype="B", name="y[%s,%s]"%(i,j))
            
    for j in Warehouses:
        for k in order_id:
            #A[k] = model.addVar(obj=0, vtype="C", name="A[%s]"%(k))
            z[j,k] = model.addVar(obj=0, vtype="B", name="z[%s,%s]"%(j,k))

    for j in Warehouses: 
        for k in S_k.keys():  
            for i in sku_id:
                x[i,j,k] = model.addVar(obj=0, vtype="B", name="x[%s,%s, %s]"%(i,j,k))     
    model.update()
    
    I_k = {}
    W_k = {}
    for k in S_k.keys():
        I_k[k] = len(S_k[k])
        W_k[k] =  gp.quicksum(z[jj,k] for jj in Warehouses)
    
    # all SKUs must be allocated to at least one warehouse (all skus bought)
    for i in sku_id: #list({x for l in S_k.values() for x in l}):
        model.addConstr(gp.quicksum(y[i,j] for j in Warehouses), ">=", 1, name="Allocate[%s]"%i)
    
    # no warehouse can contain more or less SKUs than it is specified in its capacity
    for j in Warehouses:
         model.addConstr(gp.quicksum(y[i,j] for i in sku_id), "<=", M_j[j], name="Max[%s]"%i)
         
    for j in Warehouses:
        model.addConstr(gp.quicksum(y[i,j] for i in sku_id), ">=", N_j[j], name="Min[%s]"%j)
        #model.addConstr(gp.quicksum(z[j,k] for i in order_id), ">=", 1, name="order[%s]"%j)
    
    #SKU required by a given order is shipped from exactly one of the warehouses                                                
    for k, values in S_k.items():  
        for i in values:
            model.addConstr(gp.quicksum(x[i,j,k] for j in Warehouses), "==", 1, name="shipped[%s,%s]"%(i,k))
    
    for j in Warehouses: 
        for k, values in S_k.items():  
            for i in values:
                #that SKUs will be shipped from warehouses where they have been allocated
                model.addConstr(x[i,j,k], "<=", y[i,j], "loc")
                #that there will be a shipment from every warehouse where there is at least one SKU to ship
                model.addConstr(x[i,j,k], "<=", z[j,k], "ship")
         
    model.setObjective(gp.quicksum(gp.quicksum(x[ii,j,k]*surface_i[ii] for ii in values) - F_packing( gp.quicksum(x[ii,j,k] for ii in values) ) for j in Warehouses for k, values in S_k.items() ))
                                   
    model.update()
    model.__data = x,y,z
                      
    model.ModelSense = GRB.MINIMIZE   
    model.Params.TimeLimit = 3600
    model.optimize()
    
    print("Pack optimal", model.objVal)
    W,O,S = intialize(Warehouses, M_j, N_j,S_k,sku_id)
    for j in Warehouses: 
        loc = W.get_warehouse_based_on_ID(j)
        loc.sents_orders = list(dict.fromkeys([k  for k, values in S_k.items() for i in values if x[i,j,k].x == 1]))
        loc.holds_products = list(dict.fromkeys([i  for k, values in S_k.items() for i in values if x[i,j,k].x == 1]))
    
    # for k, values in S_k.items():  
    #     cus =  O.get_order_based_on_ID(k)
    #     cus.warehouses_used = list(dict.fromkeys([j for j in Warehouses for i in values if x[i,j,k].x == 1]))
    
    for i in sku_id:
        sup =  S.get_product_based_on_ID(i)
        sup.in_warehouse = list(dict.fromkeys([j for j in Warehouses for k in S_k.keys() if x[i,j,k].x == 1]))
    
    hold_prod = []
    for j in reversed(Warehouses): 
        loc = W.get_warehouse_based_on_ID(j)
        hold_prod += loc.holds_products 
    
    not_placed = set(hold_prod) ^ set(sku_id)
    print('not placed product', len(not_placed))
    for to_place in not_placed: 
        for j in reversed(Warehouses): 
            loc = W.get_warehouse_based_on_ID(j)
            if  len(loc.holds_products) < loc.max_cap: 
                loc.holds_products.append(to_place)
                break
    
    return W,O,S
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
    #                 all_combo_w.append(combination_w)
    #     k.warehouses_combinations =  all_combo_w
        
    # print("Pack optimal", model.objVal)
    # #total_pack = model.objVal
        
    # total_cost = 0
    # total_CO2 = 0 
    # total_pack = 0
    # for w in W.warehouse_dict.values():
    #     total_cost += sum([D_in_cost[sku,w.ID] for sku in w.holds_products])
    #     total_CO2  += sum([D_in_CO2[sku,w.ID] for sku in w.holds_products])
            
    # splits  = dict.fromkeys(range(W.nr_of_warehouses), 0)
    # nr_shipment_per_w   = dict.fromkeys(range(W.nr_of_warehouses), 0)
    # for k in O.order_dict.values(): 
    #     splits[len(k.warehouses_used)-1] += 1
    #     W_kr =  len(k.warehouses_used)
    #     I_kr = len(k.purchased_items)
    #     if reduction == 'A1':
    #             F_sr = 1-(I_kr - W_kr)*Q
    #     #model.params.NonConvex = -1
    #     if reduction == 'A2': 
    #             F_sr = 1 - (I_kr/W_kr - 1)*Q
    #     total_cost_sub =0
    #     total_CO2_sub  =0
    #     for wa in k.warehouses_used: 
    #         dist = D_out[wa,k.ID]
    #         weight = 0
    #         surface = 0
    #         pack_to = 0
    #         for qq in k.purchased_items:
    #             if x[qq,wa,k.ID].x == 1:
    #                 weight += weigth_dict[qq]
    #                 surface += surface_i[qq]
    #                 pack_to += 1
            
    #         total_cost_sub +=  weight * dist * C_km_jk
    #         total_CO2_sub  +=  weight * dist * E_km_jk
    #         total_pack += surface - F_packing(pack_to)
        
    #     total_cost +=  total_cost_sub *  F_sr
    #     total_CO2  +=  total_CO2_sub *  F_sr
    #     for n in  k.warehouses_used: 
    #         nr_shipment_per_w[n] += 1
            
    # print("Pack calculated", total_pack)   
    # ship = sum([(k+1)*v for k,v in splits.items()])
    # avg_ship = ship/O.nr_of_orders
    # avg_fulfill_option = sum([len(k.warehouses_combinations) for k in O.order_dict.values()])/O.nr_of_orders

    # per_split = (sum(list(splits.values())[1:])/O.nr_of_orders)*100
    
    # result_names = ['#Orders','#Products','#Warehouses','Capacities','#Shipments','Total cost', 'Total CO2','Total Pack','% of order split'] + [f'#Order with {a} splits' for a in splits.keys()] + ['Avg #shipments per order']+ ['Avg fulfillment options per order']+ [f'#Order from W{a}' for a in nr_shipment_per_w.keys()] + ['runtime'] 
    # result_list = [O.nr_of_orders]+[S.nr_of_products]+[W.nr_of_warehouses]+[[A.max_cap for A in W.warehouse_dict.values()]]+[ship]+[round(total_cost,2)]+[round(total_CO2,2)]+[round(total_pack,6)]+[round(per_split,3)] + list(splits.values())+ [round(avg_ship,3)] + [round(avg_fulfill_option,3)] + list(nr_shipment_per_w.values()) + [time.time() - start_time]
    
    # return result_names, result_list