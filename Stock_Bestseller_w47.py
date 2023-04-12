# -*- coding: utf-8 -*-


import pandas as pd 
import numpy as np 
from Stock_Bestseller_classes import *
from Fake_Data_Generator import *
from Stock_Greedy_Seed_w51 import *
from Order_fulfill import *
import copy
import itertools
import time
import math
import random
import multiprocessing 
from functools import partial



def initialize_warehouse(Warehouses, M_j, N_j):
    W = warehouses_list()    
    for j in Warehouses:
        ID        = j
        max_cap   = M_j[j]
        min_cap   = N_j[j]
        w = warehouse(ID, max_cap, min_cap)
        W.add_warehouse(w) 
    return  W

def initialize_orders(S_k):
    O = orders_list()
    for k, purchased_i in S_k.items():
        ID                = k
        purchased_items   = purchased_i
        o = order(ID, purchased_items)
        O.add_order(o)  
    return  O

def initialize_products(sku_id):
    S = products_list()
    for i in sku_id:
        ID        = i
        s = product(ID)
        S.add_product(s)   
    return  S

def intialize(Warehouses, M_j, N_j,S_k,sku_id,):
     W = initialize_warehouse(Warehouses, M_j, N_j)
     O = initialize_orders(S_k)
     S = initialize_products(sku_id)
     return W,O,S
 
def F_packing(x):
       a = x
       b = x
       f = 16*a*b - 14*a
       return f 
            
def Bestseller(W,O,S,product_count, D_in_cost,D_in_CO2,D_out, C_km_jk, E_km_jk,Dist, surface_i, weigth_dict, reduction,Q):
    random.seed(45678)
    B = W.B_bestselling(S.nr_of_products)
    print('    B bestselling products', B)

    bestselling_products = S.times_orderd_descending(product_count)
    C = O.matrix_C(O.matrix_R())
    
    #copy of warehouses
    Sub_W = warehouses_list()
    for copy_w in W.warehouse_dict.values():
        Sub_W.add_warehouse(copy_w)
    
    #copy of products
    Sub_S = products_list()
    for copy_s in S.product_dict.values():
        Sub_S.add_product(copy_s)

    
    value_b = len([*filter(lambda x: x < B, [j.max_cap for j in Sub_W.warehouse_dict.values()] )])
    while value_b > 0:
        for j in Sub_W.warehouse_dict.values():
            if j.max_cap < B:
                for best_i in bestselling_products[:j.max_cap]:
                    j.add_product_to_warehouse(best_i)
                    S.get_product_based_on_ID(best_i).in_warehouse.append(j.ID)
                Sub_W.remove_warehouse(j.ID)    
                break
        B = Sub_W.B_bestselling(S.nr_of_products)
        value_b = len([*filter(lambda x: x < B, [j.max_cap for j in Sub_W.warehouse_dict.values()] )])
       
    if B == 0:
        #print('Greedy seed heuristic')
        #print()
        greedy_seed(C,W,O,S,Sub_W,Sub_S)
    
    elif B > 0: 
      
        #print('Bestseller heuristic')
        #print()
        
        Sub_W_dict = Sub_W.warehouse_cap_descending()
        skus_volume = product_count
       
        #bestselling products to all warehouses    
        skus_left = Sub_S.times_orderd_descending( skus_volume)    
        for j in Sub_W_dict.values():
            for best_i in bestselling_products[:int(B)]:
                j.add_product_to_warehouse(best_i)
                S.get_product_based_on_ID(best_i).in_warehouse.append(j.ID)
                if best_i in Sub_S.product_dict.keys():
                    Sub_S.remove_product(best_i)
                    #skus_volume.pop(best_i)
                    
        
        # #zero sales skus to random warehouse
        # w_times_chosen              = dict.fromkeys(range(W.nr_of_warehouses), 0)
        # skus_volume_zero = [key  for key,value in product_count.items() if value == 0]
        # for zero_i in  skus_volume_zero:
        #   j =  random.choice(list(Sub_W_dict.values()))
        #   while w_times_chosen[j.ID] >= int(len(skus_volume_zero)/2) and j.left_over_capacitie(j.holds_products)  == 0 : 
        #       j =  random.choice(list(Sub_W_dict.values()))
        #   j.add_product_to_warehouse(zero_i)
        #   S.get_product_based_on_ID(zero_i).in_warehouse.append(j.ID)
        #   w_times_chosen[j.ID] += 1
        #   if zero_i in Sub_S.product_dict.keys():
        #       Sub_S.remove_product(zero_i)
        
        #left over skus based on rule
        new_skus_volume = {k:v for k,v in product_count.items() if k in list(Sub_S.product_dict.keys())}
        skus_left = Sub_S.times_orderd_descending(new_skus_volume)                      
        if Dist == 0: 
            #print("Based on coappearance matrix")
            #print()
            for i in  skus_left:               
                Sub_W_dict = Sub_W.warehouse_cap_descending()
                if new_skus_volume[i] > 0:
                    coap_j = {}
                    for j in Sub_W_dict.values():
                        holds_products =  [x for x in j.holds_products if x < C.shape[0]]
                        coappearances = sum([C[i,hold_i] for hold_i in holds_products]) 
                        coap_j[j] = coappearances/len(holds_products)
                    
                    max_avg_coap_j = sorted(coap_j, key=coap_j.get, reverse=True) 
                    max_j = max_avg_coap_j[0]
                else: 
                    #coap_j = {j : 0  for j in Sub_W_dict.values()}
                    
                    #max_avg_coap_j = sorted(coap_j, key=coap_j.get, reverse=True) 
                    max_j = random.choice(list(Sub_W_dict.values()))

                if max_j.left_over_capacitie(max_j.holds_products) > 0: 
                    max_j.add_product_to_warehouse(i)
                    S.get_product_based_on_ID(i).in_warehouse.append(max_j.ID)
                    Sub_S.remove_product(i)
                    if max_j.left_over_capacitie(max_j.holds_products) == 0:
                        Sub_W.remove_warehouse(max_j.ID)
        elif Dist == 1: 
              D_all_out = O.matrix_D_all_out(O.matrix_R(), D_out)
              #print("Based on cost weigthed-distance matrix")
              #print()
              for i in  skus_left:   
                  Sub_W_dict = Sub_W.warehouse_cap_descending()
                  if new_skus_volume[i] > 0:
                      dis_coap_j = {}
                      for j in Sub_W_dict.values():
                              holds_products = [x for x in j.holds_products if x < C.shape[0]]
                              W_kr = 1
                              I_kr = math.ceil((sum([C[i,hold_i] for hold_i in holds_products])+C[i,i])/C[i,i])
                              if reduction == 'A1':
                                    F_sr = 1-(I_kr - W_kr)*Q
                              #model.params.NonConvex = -1
                              if reduction == 'A2': 
                                    F_sr = 1 - (I_kr/W_kr - 1)*Q
                                    
                              tot_in = D_in_cost[i,j.ID] 
                              tot_out = D_all_out[j.ID,i] * weigth_dict[i] #* C_km_jk
                              
                              
                              #fourth method
                              dis_coap_j[j] = tot_in + tot_out*F_sr #
                              
                      max_avg_dis_coap_j = sorted(dis_coap_j, key=dis_coap_j.get, reverse=False) 
                      max_j = max_avg_dis_coap_j[0]
                        
                  else: 
                      max_j = random.choice(list(Sub_W_dict.values()))
                        #dis_coap_j = {j: D_in_cost[i,j.ID] for j in Sub_W_dict.values()}
                 
                
                  if max_j.left_over_capacitie(max_j.holds_products) > 0: 
                      max_j.add_product_to_warehouse(i)
                      S.get_product_based_on_ID(i).in_warehouse.append(max_j.ID)
                      Sub_S.remove_product(i)
                      if max_j.left_over_capacitie(max_j.holds_products) == 0:
                         Sub_W.remove_warehouse(max_j.ID)     
                       
        elif Dist == 2: 
              D_all_out = O.matrix_D_all_out(O.matrix_R(), D_out)
              #print("Based on CO2 weigthed-distance matrix")
              #print()
              for i in  skus_left:              
                  Sub_W_dict = Sub_W.warehouse_cap_descending()
                  if new_skus_volume[i] > 0:
                      dis_coap_j = {}
                      for j in Sub_W_dict.values():
                          holds_products =  [x for x in j.holds_products if x < C.shape[0]]
                          W_kr = 1
                          I_kr = math.ceil((sum([C[i,hold_i] for hold_i in holds_products])+C[i,i])/C[i,i])
                          if reduction == 'A1':
                                    F_sr = 1-(I_kr - W_kr)*Q
                            #model.params.NonConvex = -1
                          elif reduction == 'A2': 
                                    F_sr = 1 - (I_kr/W_kr - 1)*Q
                                    
                          tot_in = D_in_CO2[i,j.ID] 
                          tot_out = D_all_out[j.ID,i] * weigth_dict[i] * E_km_jk
                          dis_coap_j[j]  = tot_in + tot_out*F_sr #
                  else: 
                      dis_coap_j = {j: D_in_CO2[i,j.ID] for j in Sub_W_dict.values()}
                          
                  max_avg_dis_coap_j = sorted(dis_coap_j, key=dis_coap_j.get, reverse=False) 
                  max_j = max_avg_dis_coap_j[0]
          
                  if max_j.left_over_capacitie(max_j.holds_products) > 0: 
                      max_j.add_product_to_warehouse(i)
                      S.get_product_based_on_ID(i).in_warehouse.append(max_j.ID)
                      Sub_S.remove_product(i)
                      if max_j.left_over_capacitie(max_j.holds_products) == 0:
                         Sub_W.remove_warehouse(max_j.ID)     
        elif Dist == 3: 
            #print("Based on surface matrix")
            #print()
            for i in  skus_left:   
                Sub_W_dict = Sub_W.warehouse_cap_descending()
                if new_skus_volume[i] > 0:
                    coap_j = {}
                    for j in Sub_W_dict.values():
                        holds_products =  [x for x in j.holds_products if x < C.shape[0]]
                        avg_items_pack_together = math.ceil((sum([C[i,hold_i] for hold_i in holds_products])+C[i,i])/C[i,i])
                        coappearances =  F_packing(avg_items_pack_together)
                        coap_j[j] = new_skus_volume[i] * (surface_i[i]  - coappearances)
                        #coappearances = sum([C[i,hold_i] * F_packing(2) for hold_i in holds_products]) 
                        #if not C[i,i] == 0: 
                        #else:
                                #coap_j[j] = 0 
                    max_avg_coap_j = sorted(coap_j, key=coap_j.get, reverse=False) 
                    max_j = max_avg_coap_j[0]
                else: 
                    #coap_j = {j: 0  for j in Sub_W_dict.values()}  
                    max_j = random.choice(list(Sub_W_dict.values()))
                
                if max_j.left_over_capacitie(max_j.holds_products) > 0: 
                    max_j.add_product_to_warehouse(i)
                    S.get_product_based_on_ID(i).in_warehouse.append(max_j.ID)
                    Sub_S.remove_product(i)
                    if max_j.left_over_capacitie(max_j.holds_products) == 0:
                        Sub_W.remove_warehouse(max_j.ID) 

def results(W,O,S,D_in_cost,D_in_CO2,D_out, C_km_jk, E_km_jk,Dist, surface_i, weigth_dict,reduction,Q,type_res):    

    #order fulfillment
    if Dist in [1,2,3]:
        order_fulfill_min_cost_co2_pack(O,W,surface_i,D_out,weigth_dict,C_km_jk,E_km_jk,reduction,Q,Dist)
        
    if Dist == 0:
        order_fulfill_min_split(O,W,surface_i,D_out,weigth_dict,C_km_jk,E_km_jk,reduction,Q)
       
    total_cost = 0
    total_cost_in = 0
    total_CO2 = 0 
    total_CO2_in = 0
    total_pack = 0
                
    for w in W.warehouse_dict.values():
        total_cost_in += sum([D_in_cost[sku,w.ID] for sku in w.holds_products]) # * aantal_ton_per_truck[sku]
        total_CO2_in  += sum([D_in_CO2[sku,w.ID]  for sku in w.holds_products])
                
    total = 0
    splits              = dict.fromkeys(range(W.nr_of_warehouses), 0)
    nr_combo_per_split  = dict.fromkeys(range(W.nr_of_warehouses), 0)
    nr_shipment_per_w   = dict.fromkeys(range(W.nr_of_warehouses), 0)
    nr_combo_per_w      = dict.fromkeys(range(W.nr_of_warehouses), 0)
    w_can_send_hole_orders     = dict.fromkeys(range(W.nr_of_warehouses), 0)
    
    
    nr_fulfill_options = 0
    for k in O.order_dict.values(): 
        total_cost  +=   k.total_order_cost
        total_CO2   +=   k.total_order_CO2
        total_pack  +=  k.total_order_pack
        nr_fulfill_options +=  len(k.warehouses_combinations)
        splits[len(k.warehouses_used)-1] += 1
        if k.min_nr_shipments == 1000:
            total += 1
        for n in  k.warehouses_used: 
            nr_shipment_per_w[n] += 1
        for l in k.warehouses_combinations:
            if len(l) == 1:
                w_can_send_hole_orders[l[0]] += 1
                break
                
            
    per_split = (sum(list(splits.values())[1:])/O.nr_of_orders)*100
    avg_ship = sum([(k+1)*v for k,v in splits.items()])/O.nr_of_orders
    ship =  sum([(k+1)*v for k,v in splits.items()])
    avg_fulfill_option =nr_fulfill_options/O.nr_of_orders
    
    #total_pack = sum([k.total_order_pack for k in O.order_dict.values()])
    
    if type_res == 1: 
        result_names = ['#Shipments','Total weigth dist in', 'Total weigth dist out','Total Pack','% of order split'] + [f'#Order with {a} splits' for a in splits.keys()] + ['Avg #shipments per order']+ ['Avg fulfillment options per order']+ [f'#Order from W{a}' for a in nr_shipment_per_w.keys()] + [f'#non split order from W{a}' for a in nr_shipment_per_w.keys()] + ['Avg #Warehouse per non split order'] 
        result_list = [ship]+[round(total_cost_in,2)]+[round(total_cost,2)]+[round(total_pack,6)]+[round(per_split,3)] + list(splits.values())+ [round(avg_ship,3)] + [round(avg_fulfill_option,3)] + list(nr_shipment_per_w.values()) +  list(w_can_send_hole_orders.values()) + [sum(w_can_send_hole_orders.values())/O.nr_of_orders]
    else:
        if Dist == 0:
            result_names = ['Min split - #ship','Min split - WD tkm','Min split - surface cm2']
            result_list = [sum([(k+1)*v for k,v in splits.items()]),sum([k.total_order_CO2 for k in O.order_dict.values()]),sum([k.total_order_pack for k in O.order_dict.values()])]
        elif Dist == 1:
            
            result_names = ['Min WD - #ship','Min WD - WD tkm','Min WD - surface cm2']
            result_list =  [sum([(k+1)*v for k,v in splits.items()]),sum([k.total_order_CO2 for k in O.order_dict.values()]),sum([k.total_order_pack for k in O.order_dict.values()])]
            
        elif Dist == 2:
            result_names = ['Total CO2']
            result_list = [sum([k.total_order_CO2 for k in O.order_dict.values()]),sum([k.total_order_pack for k in O.order_dict.values()])]
        
        elif Dist == 3:
            result_names = ['Min pack- #ship','Min pack- WD tkm','Min pack - surface cm2']
            result_list =  [sum([(k+1)*v for k,v in splits.items()]),sum([k.total_order_CO2 for k in O.order_dict.values()]),sum([k.total_order_pack for k in O.order_dict.values()])]
              
    return result_names, result_list
    

# def main(Warehouses, M_j, N_j,S_k,sku_id, C_km_ij, E_km_ij, C_km_jk, E_km_jk, dim_product_dict):
#     #DIST = 1  
#     W,O,S = intialize(Warehouses, M_j, N_j,S_k,sku_id)
#     D_in, D_out = distance_matrix(Warehouses,sku_id,S_k)
#     Bestseller(W,O,S,D_in,D_out,C_km_ij, E_km_ij, C_km_jk, E_km_jk,Dist, dim_product_dict)
#     name,res = results(W,O,S,D_in,D_out, C_km_ij, E_km_ij, C_km_jk, E_km_jk,Dist, dim_product_dict)
    
# if __name__ == '__main__':
#   main(Warehouses, M_j, N_j,S_k,sku_id,C_km_ij, E_km_ij, C_km_jk, E_km_jk)



  
  

    