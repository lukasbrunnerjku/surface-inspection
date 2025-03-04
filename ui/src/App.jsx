import { useEffect, useState } from "react";
// import './App.css'
// the above css file is not needed anymore for now

// cd ui
// npm run dev


export default function App() {
  const [data, setData] = useState({ text: "", image_base64: "" });

  useEffect(() => {
    fetch("http://localhost:5000/api/data")
      .then((response) => response.json())
      .then((data) => setData(data))
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  return (
    <div className="flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold mb-4">Flask & React Image Viewer</h1>
      {data.text && <p className="mb-4 text-lg">{data.text}</p>}
      {data.image_base64 && (
        <img src={data.image_base64} alt="Fetched from backend" className="rounded shadow-lg" />
      )}
    </div>
  );
}
