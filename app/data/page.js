'use client';
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const OrganizationData = () => {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        // Fetch organizations from the API
        const response = await axios.get('https://api.catastrophe.world/organizations/?page=1&per_page=12&stateorprovince=TX&sortby=asc-name&rating=4');
        setOrganizations(response.data);
        setLoading(false); // Set loading to false after successful fetch
      } catch (error) {
        console.error('Error fetching organizations:', error);
        setError('Error fetching organizations. Please try again later.'); // Set error message
        setLoading(false); // Set loading to false on error
      }
    };

    fetchOrganizations();
  }, []);

  if (loading) {
    return <div>Loading...</div>; // Show loading indicator while fetching data
  }

  if (error) {
    return <div>Error: {error}</div>; // Show error message if fetch fails
  }

  return (
    <div className="container mx-auto">
      <h1 className="text-2xl font-bold text-center my-4">Organizations</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {organizations.map((org, index) => (
          <div key={index} className="bg-gray-100 p-4 rounded-lg shadow-md">
            <h2 className="text-lg font-semibold mb-2">{org.name}</h2>
            <p className="text-gray-600 mb-2">Location: {org.location}</p>
            <p className="text-gray-600 mb-2">Rating: {org.rating}</p>
            <p className="text-gray-600 mb-2">Contact: {org.contact}</p>
            {/* Add more fields as needed */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrganizationData;
