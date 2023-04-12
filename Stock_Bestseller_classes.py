# -*- coding: utf-8 -*-
"""
Created on Fri Dec  9 12:41:47 2022

@author: Den Daas
"""

import pandas as pd
import numpy as np 
import copy 
import scipy.sparse as sp

class warehouse:
    def __init__(self, ID, max_cap, min_cap):
      self.ID = ID
      self.max_cap = max_cap
      self.min_cap = min_cap
      self.holds_products = []
      self.sents_orders = []
      
    def get_max_cap(self):
        return self.max_cap

    def get_min_cap(self):
        return self.min_cap
  
    def get_holds_products(self):
        return self.holds_products
    
    def add_product_to_warehouse(self, product):
        return self.holds_products.append(product)
    
    def get_sent_orders(self):
        return self.sents_orders
    
    def sent_order_from_Warehouse(self, order):
        return self.sents_orders.append(order)
    
    def left_over_capacitie(self,holds_products):
        return self.max_cap - len(holds_products)
    

class warehouses_list:
    def __init__(self):
      self.warehouse_list = []  
      self.warehouse_dict = {}
      self.nr_of_warehouses = 0
      
    def add_warehouse(self, warehouse):
      self.warehouse_dict[warehouse.ID] = warehouse
      self.warehouse_list.append(warehouse)
      self.nr_of_warehouses += 1
    
    def copy_warehouse_list(self):
        return self
    
    def remove_warehouse(self, warehouse_ID):
      del self.warehouse_dict[warehouse_ID]
      self.nr_of_warehouses += -1
          
    def get_warehouse_based_on_ID(self, ID): 
      return self.warehouse_dict[ID]
  
    def B_bestselling(self,nr_products):
        total_max_cap = 0
        if self.nr_of_warehouses > 1: 
            for w in self.warehouse_dict.values():
                total_max_cap += w.max_cap
            B = (total_max_cap - nr_products)/(self.nr_of_warehouses-1)
        else:
            B = 0 
        return B
        
    def warehouse_cap_ascending(self):
        cap = {}
        for j,w in self.warehouse_dict.items():
            cap[j] = w.max_cap
        structure = sorted(cap, key=cap.get, reverse=False)
        return dict(sorted(self.warehouse_dict.items(), key=lambda pair:  structure.index(pair[0])))
        
    def warehouse_cap_descending(self): 
        cap = {}
        for j,w in self.warehouse_dict.items():
            cap[j] = w.max_cap
        structure = sorted(cap, key=cap.get, reverse=True)
        return  dict(sorted(self.warehouse_dict.items(), key=lambda pair:  structure.index(pair[0])))
        
        
  
 
    
 
class order:
    def __init__(self, ID, purchased_items):
      self.ID = ID
      self.purchased_items = purchased_items
      self.min_nr_shipments = 1000
      self.warehouses_used = None
      self.warehouses_combinations = []
      self.total_order_cost = None
      self.total_order_CO2 = None
      self.total_order_pack = None
      self.total_order_split = None
      
    def add_warehouses_used(self, warehouse_id):
        if self.warehouses_used == None:
            self.warehouses_used = [warehouse_id]
        else:
            self.warehouses_used.append(warehouse_id)
      
class orders_list: 
    def __init__(self):
      self.order_l = [] 
      self.order_dict = {}
      self.nr_of_orders = 0
      
    def add_order(self, order):
      self.order_l.append(order.ID)
      self.order_dict[order.ID] = order
      self.nr_of_orders += 1
      
    def remove_order(self, order):
      del self.order_dict[order.ID]
      self.nr_of_orders += -1
          
    def get_order_based_on_ID(self, ID): 
      return self.order_dict[ID]
    
   
    
    def matrix_R(self):
        row_ind = [k for k, v in self.order_dict.items() for t in range(len(v.purchased_items))]
        col_ind = [i for ids in self.order_dict.values() for i in ids.purchased_items]
        R = sp.csr_matrix(([1]*len(row_ind), (row_ind, col_ind)))
        R.data = np.nan_to_num(R.data, copy=False)
        #df_out = pd.DataFrame(data=sp.csr_matrix.todense(R))
        #df_out.to_excel('4Results\\R_mini_test.xlsx', index=False)
        return R
    
    def matrix_C(self, matrix_R):
        C = np.dot(matrix_R.T, matrix_R)
        C.data = np.nan_to_num(C.data, copy=False)
        #df_out = pd.DataFrame(data=sp.csr_matrix.todense(C))
        #df_out.to_excel('4Results\\C_mini_test.xlsx', index=False)
        #print(C.shape)
        return C
    
    def matrix_D_item(self, matrix_R, D_in, D_out):
        hel = np.dot(D_out,matrix_R)
        D_item = (hel.tocsr() + D_in.T.tocsr()).tolil()
        #df_out = pd.DataFrame(data=sp.csr_matrix.todense(D_item))
        #df_out.to_excel('4Results\\D_mini_test.xlsx', index=False)
        return D_item
    
    def matrix_D_all_out(self, matrix_RR, D_out):
        D_all_out = np.dot(D_out,matrix_RR)
       
        #df_out = pd.DataFrame(data=sp.csr_matrix.todense(D_item))
        #df_out.to_excel('4Results\\D_mini_test.xlsx', index=False)
        return D_all_out
        
        





class product:
    def __init__(self, ID ):
      self.ID = ID
      self.in_warehouse = []
      
class products_list: 
    def __init__(self):
      self.product_l = []
      self.product_dict = {}
      self.nr_of_products = 0
      
    
    def copy_product_list(self):
        return self
      
    def add_product(self, product):
      self.product_l.append(product.ID)
      self.product_dict[product.ID] = product
      self.nr_of_products += 1
      
    def remove_product(self, product_id):
      del self.product_dict[product_id]
      self.nr_of_products +=  -1
         
    def get_product_based_on_ID(self, ID): 
      return self.product_dict[ID]
  
    def x_times_orderd(self,orders):
        times_orderd = {}
        for i in self.product_dict.keys():
            times_orderd[i] = 0 
            for order in orders.order_dict.values():
                if i in order.purchased_items:
                    times_orderd[i] += 1 
        return  times_orderd
    
    def times_orderd_descending(self,times_orderd):
        return sorted(times_orderd, key=times_orderd.get, reverse=True)
        
    def times_order_ascending(self,times_orderd):
        return sorted(times_orderd, key=times_orderd.get, reverse=False)
    
   
        
    