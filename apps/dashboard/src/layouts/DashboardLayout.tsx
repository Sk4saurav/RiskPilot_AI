import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Shield, LayoutDashboard, Database, Activity } from 'lucide-react';

export const DashboardLayout = () => {
  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>RiskPilot</h1>
          <div className="subtitle">Analyst Console</div>
        </div>
        
        <nav className="nav-links">
          <div className="subtitle" style={{ marginBottom: '8px' }}>Overview</div>
          <NavLink 
            to="/cases" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Shield size={18} />
            Case Queue
          </NavLink>
          <NavLink 
            to="/analytics" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard size={18} />
            Analytics
          </NavLink>
          <NavLink 
            to="/integrations" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Database size={18} />
            Integrations
          </NavLink>
          <NavLink 
            to="/system-status" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Activity size={18} />
            System Status
          </NavLink>
        </nav>
      </aside>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};
