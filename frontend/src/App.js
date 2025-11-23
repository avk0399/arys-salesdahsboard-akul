import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, ShoppingCart, Package } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5001/api';  // UPDATED PORT!

const SalesDashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [salesOverTime, setSalesOverTime] = useState([]);
  const [salesByCategory, setSalesByCategory] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [productPerformance, setProductPerformance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timePeriod, setTimePeriod] = useState('month');

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

  useEffect(() => {
    fetchAllData();
  }, [timePeriod]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [kpisRes, salesTimeRes, categoryRes, customersRes, productRes] = await Promise.all([
        fetch(`${API_BASE_URL}/kpis`),
        fetch(`${API_BASE_URL}/sales-over-time?period=${timePeriod}`),
        fetch(`${API_BASE_URL}/sales-by-category`),
        fetch(`${API_BASE_URL}/top-customers?limit=5`),
        fetch(`${API_BASE_URL}/product-performance`)
      ]);

      const kpisData = await kpisRes.json();
      const salesTimeData = await salesTimeRes.json();
      const categoryData = await categoryRes.json();
      const customersData = await customersRes.json();
      const productData = await productRes.json();

      setKpis(kpisData);
      setSalesOverTime(salesTimeData);
      setSalesByCategory(categoryData);
      setTopCustomers(customersData);
      setProductPerformance(productData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const KPICard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold mt-2">{value}</p>
        </div>
        <div className="p-3 rounded-full" style={{ backgroundColor: `${color}20` }}>
          <Icon size={24} color={color} />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Sales Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">Real-time insights into your sales performance</p>
        </div>

        {/* KPI Cards */}
        {kpis && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPICard
              title="Total Revenue"
              value={formatCurrency(kpis.total_revenue || 0)}
              icon={DollarSign}
              color="#10b981"
            />
            <KPICard
              title="Total Orders"
              value={(kpis.total_orders || 0).toLocaleString()}
              icon={ShoppingCart}
              color="#3b82f6"
            />
            <KPICard
              title="Average Order Value"
              value={formatCurrency(kpis.avg_order_value || 0)}
              icon={TrendingUp}
              color="#f59e0b"
            />
            <KPICard
              title="Total Quantity"
              value={(kpis.total_quantity || 0).toLocaleString()}
              icon={Package}
              color="#8b5cf6"
            />
          </div>
        )}

        {/* Time Period Selector */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <label className="text-sm font-medium text-gray-700 mr-3">Time Period:</label>
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="day">Daily</option>
            <option value="month">Monthly</option>
            <option value="quarter">Quarterly</option>
            <option value="year">Yearly</option>
          </select>
        </div>

        {/* Sales Over Time Chart */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Sales Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Line type="monotone" dataKey="total_sales" stroke="#3b82f6" strokeWidth={2} name="Total Sales" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Sales by Category */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Sales by Status</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={salesByCategory}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, percent }) => `${category}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="total_sales"
                >
                  {salesByCategory.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Top Customers */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Top Customers/Orders</h2>
            <div className="space-y-3">
              {topCustomers.map((customer, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-semibold mr-3">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">
                        {customer.customer_name || `Order #${customer.order_id}`}
                      </p>
                      <p className="text-sm text-gray-500">
                        {customer.order_count ? `${customer.order_count} orders` : `${customer.line_items} items`}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-800">{formatCurrency(customer.total_sales)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Product Performance */}
        {productPerformance.length > 0 && !productPerformance[0].message && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Product Performance</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={productPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="product" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
                <Bar dataKey="total_sales" fill="#3b82f6" name="Total Sales" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Dashboard updates in real-time • Last updated: {new Date().toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default SalesDashboard;