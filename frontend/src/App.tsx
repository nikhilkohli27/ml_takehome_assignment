import { useState } from 'react';

interface PredictionResponse {
  prediction: string;
  no_show_probability: number;
  risk_level: 'High' | 'Medium' | 'Low';
}

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    age: 45,
    gender: 'F',
    neighbourhood: 'JARDIM CAMBURI',
    leadTime: 5
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    const today = new Date();
    const apptDate = new Date();
    apptDate.setDate(today.getDate() + formData.leadTime);

    const payload = {
      Age: Number(formData.age),
      Gender: formData.gender,
      Neighbourhood: formData.neighbourhood,
      ScheduledDay: today.toISOString(),
      AppointmentDay: apptDate.toISOString(),
      // Defaults
      OnGovtWelfareBenefits: 0, Hypertension: 0, Diabetes: 0, Alcoholism: 0, Handicapped: 0, SMS_received: 0
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      alert("Error: Backend not running.");
    } finally {
      setLoading(false);
    }
  };

  // Helper for colors
  const getRiskStyles = (risk: string) => {
    if (risk === 'High') return 'bg-red-50 border-red-200 text-red-700';
    if (risk === 'Medium') return 'bg-yellow-50 border-yellow-200 text-yellow-700'; // Added Yellow!
    return 'bg-green-50 border-green-200 text-green-700';
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">🏥 Patient Check-In</h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Patient Age</label>
            <input 
              type="number" 
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: Number(e.target.value)})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Gender</label>
            <select 
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
              value={formData.gender}
              onChange={(e) => setFormData({...formData, gender: e.target.value})}
            >
              <option value="F">Female</option>
              <option value="M">Male</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Days until Appointment</label>
            <input 
              type="number" 
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
              value={formData.leadTime}
              onChange={(e) => setFormData({...formData, leadTime: Number(e.target.value)})}
            />
          </div>

          <button 
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 font-semibold transition-colors disabled:bg-blue-300"
          >
            {loading ? 'Analyzing...' : 'Predict Risk'}
          </button>
        </form>

        {result && (
          <div className={`mt-6 p-4 rounded-lg border ${getRiskStyles(result.risk_level)}`}>
            <h3 className="font-bold text-lg">{result.prediction}</h3>
            <p>No-Show Probability: <strong>{(result.no_show_probability * 100).toFixed(1)}%</strong></p>
            <p className="text-sm mt-1 uppercase tracking-wide font-semibold">{result.risk_level} Risk</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;