from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import List
import json
import sys
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv(override=True)
# from system.config import Config 

# Load config from local_settings.json
# config_loader = Config()
# config = config_loader.get_config()

    
class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
#       self.setup_database()
    
    def connect(self):
        try:
            self.pgconnection = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DATABASE'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            self.pgcursor = self.pgconnection.cursor()

            tenant_name = "tenant"+str(os.getenv('TENANT_ID'))+""
            set_path_query = f"set search_path = "+str(tenant_name)+""
            self.pgcursor.execute(set_path_query)
            print("connection successful")

        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def execute_query(self, query, data=None):
        try:
            self.pgcursor.execute(query, data)
            self.pgconnection.commit()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
            self.pgconnection.rollback()
            raise

    def get_assets_from_building(self, building_id: int) -> List[dict]:
        if not building_id:
            return "please provide the building id"
        """Get assets from the table"""
        query = """
        select name from tenant5.assets where building_id = %s
        """
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (building_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting leave history: {e}")
            return []
        
    # def create_building(self, name: str):
    #     if not name:
    #         return "please provide a name for the building"
    #     """Add a building with its name and return the new building's ID."""
    #     building_insert_query = "INSERT INTO tenant5.buildings (name) VALUES (%s) RETURNING id"
    #     try:
    #         with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
    #             cursor.execute(building_insert_query, (name))
    #             result = cursor.fetchone()[0]
    #             self.connection.commit()
    #             return result
    #     except Exception as e:
    #         print(f"Error creating building: {e}")
    #         self.connection.rollback()
    #         return None
    
    def get_or_create_building_id_by_name(self,name: str=None):
        select_query="select id from tenant5.buildings where name=%s"
        select_data=(name,)
        self.execute_query(select_query,select_data)
        building_id=self.pgcursor.fetchone()
        
        if building_id:
            print(f"inserted into buildings with name:{name}")
            return building_id[0]
        
        insert_query="INSERT INTO tenant5.buildings (name) VALUES (%s) RETURNING id"
        insert_data=(name,)
        self.execute_query(insert_query,insert_data)
        print(f"inserted into buildings with name:{name}")
        building_id=self.pgcursor.fetchone()[0]
        if building_id:
            return building_id

    
    def create_alarm_devices(self,location: str=None,alarm_system_id: int=None,alarm_device_type_id: int=None):
        
        if not location:
            return "Please provide the location"

        if not alarm_system_id:
            return "Please provide the alarm system id"
        
        if not alarm_device_type_id:
            return "Please provide the alarm device type id"
        
        query = "INSERT INTO tenant5.alarm_devices (location,alarm_system_id,alarm_device_type_id) VALUES (%s, %s, %s)  returning id"

        data = (location,alarm_system_id,alarm_device_type_id)
        
        self.execute_query(query, data)
        alarm_device_id=self.pgcursor.fetchone()[0]
        return alarm_device_id

    def create_alarm_system(self,name: str = None, building_name: str = None):
        if not name:
            return "please provide the name"
        if not building_name:
            return "Enter the building name"
        
        building_id=self.get_or_create_building_id_by_name(building_name)
        if building_id:
            query= "insert into tenant5.alarm_systems (name,building_id) values(%s,%s) returning id"
            data=(name,building_id)
            self.execute_query(query,data)
            alarm_system_id=self.pgcursor.fetchone()[0]
            if alarm_system_id:
                return f"alarm system created id: {alarm_system_id}"
        return "not created"
    
    def get_alarm_device_types_id(self,name: str=None):
        if not name:
            return "Please provide a name for the alarm device type"
        
        get_query="select id from alarm_device_types where type_name=%s"
        data=(name)
        self.execute_query(get_query,data)
        alarm_device_type_id=self.pgcursor.fetchone()[0]
        if alarm_device_type_id:
            return alarm_device_type_id
        
        insert_query="Insert into alarm_device_types (type_name) values (%s) returning id"
        insert_data=(name)
        self.execute_query(insert_query,insert_data)
        alarm_device_type_id=self.pgcursor.fetchone()[0]
        if alarm_device_type_id:
            return alarm_device_type_id
        return "not created"




db_manager = DatabaseManager()
mcp = FastMCP("BuildingManagement")
print(dir(mcp))