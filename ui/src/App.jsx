import { useState, useEffect, useRef } from "react";

// npm install framer-motion
import { motion, AnimatePresence } from "framer-motion";

// npm install react-spinners
import { BarLoader } from "react-spinners";

// cd ui
// npm run dev


export default function App() {
  const [examples, setExamples] = useState([]);
  const [loadingExamples, setLoadingExamples] = useState(true);
  const [errorFetchingExamples, setErrorFetchingExamples] = useState(false);

  const [nextItem, setNextItem] = useState({});
  const [loadingNextItem, setLoadingNextItem] = useState(true);
  const [errorFetchingNextItem, setErrorFetchingNextItem] = useState(false);
  const hasFetchedNextItem = useRef(false);  // Prevents re-fetching in debug mode

  const [dataProgress, setDataProgress] = useState(0);

  const [leftItems, setLeftItems] = useState([]);
  const [rightItems, setRightItems] = useState([]);
  const [lastDroppedIndex, setLastDroppedIndex] = useState(null);
  const [isAnimatingLeft, setIsAnimatingLeft] = useState(false);
  const [isAnimatingRight, setIsAnimatingRight] = useState(false);

  const [isOpen, setIsOpen] = useState(false);  // Popup window
  const [evalResAI, setEvalResAI] = useState({});
  const [evalResPlayer, setEvalResPlayer] = useState({});
  const [loading, setLoading] = useState(false);  // Loading bar evaluation

  const [isOn, setIsOn] = useState(false);  // Feedback toggle switch

  useEffect(() => {
    setLoadingExamples(true);
    setErrorFetchingExamples(false); // Reset error state

    fetch("http://localhost:5000/api/examples")
      .then((response) => response.json())
      .then((data) => {
        setExamples(data);
        setLoadingExamples(false);
      })
      .catch((error) => {
        console.error("Error fetching examples:", error);
        setErrorFetchingExamples(true);
        setLoadingExamples(false);
      });
  }, []);

  const fetchNextItem = () => {
    setLoadingNextItem(true); // Show "Loading..."
    setErrorFetchingNextItem(false); // Reset error state

    fetch("http://localhost:5000/api/next_item")
      .then((response) => response.json())
      .then((data) => {
        setNextItem({...data, key: data.n_seen});
        setDataProgress(Math.round(100 * nextItem.n_seen / nextItem.n_total));
        setLoadingNextItem(false);
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
        setErrorFetchingNextItem(true); // Set error state
        setLoadingNextItem(false);  // Stop loading on error
      });
  };
  
  const fetchEvaluation = async () => {
    setLoading(true); // Start loading
    try {
      const response = await fetch("http://localhost:5000/api/evaluation");
      const data = await response.json();
      setEvalResAI({...data});
    } catch (error) {
      console.error("Error fetching evaluation:", error);
    }
    setLoading(false); // Stop loading
  };
  
  const handleEvaluationClick = async () => {
    await fetchEvaluation(); // Fetch data first
    setIsOpen(true); // Open the popup after image is ready
  };

  useEffect(() => {
    if (!hasFetchedNextItem.current) {
      fetchNextItem();
      hasFetchedNextItem.current = true;
    }
  }, []);

  const handleDrop = (event, side) => {
    event.preventDefault();
    const animationDuration = 500;  // [ms]

    if (side === "left") {
      setLeftItems([nextItem, ...leftItems]);
      setIsAnimatingLeft(true);
      setTimeout(() => setIsAnimatingLeft(false), animationDuration);
    } else {
      setRightItems([nextItem, ...rightItems]);
      setIsAnimatingRight(true);
      setTimeout(() => setIsAnimatingRight(false), animationDuration);
    }
    setLastDroppedIndex(0);  // Added new element at the beginning
    fetchNextItem();  // Load next item
  };

  const allowDrop = (event) => {
    event.preventDefault();
  };

  const handleDragStart = (e) => {
    e.dataTransfer.setData("text/plain", "image");
  };

  return (
    <div className="flex flex-col items-center p-4">

      <h1 className="text-2xl font-bold mb-4">Decor Classification Challenge</h1>
      
      <p className="mt-2 mb-4whitespace-pre-wrap">
        Can you beat the AI system in classifying the presented wooden decores correctly?<br />
        The system will present you with a series of images, and you have to sort them<br />
        into the correct list via drag&drop. The example images will help you as reference.
      </p>

      {loadingExamples || errorFetchingExamples ? (
        <p>Loading...</p>
      ) : (
        <div className="flex justify-center gap-12 mt-6">
          {examples.map((example, index) => (
            <div
              key={index}
              className="flex flex-col items-center bg-gray-200 p-4 rounded-lg shadow-lg transform transition-transform duration-300 hover:scale-150"
            >
              <div className="relative overflow-hidden w-[128px] h-[128px]">
                <img
                  src={example.image_base64}
                  alt={example.label}
                  className="w-full h-full object-cover rounded"
                  onLoad={() => {
                    console.log("Examples loaded.")
                    setLoadingExamples(false);
                  }}
                  onError={() => {
                    console.log("Error loading examples.")
                    setErrorFetchingExamples(true);
                    setLoadingExamples(false);
                  }}
                />
              </div>
              <h2 className="mt-2 text-lg font-semibold">{example.label}</h2>
            </div>
          ))}
        </div>
      )}

      <div className="w-full max-w-sm mt-4 p-4 rounded-full">
        <div
          className="bg-blue-500 text-xs text-center text-black p-1 rounded-full"
          style={{ width: `${dataProgress}%` }}
        >
          {dataProgress}%
        </div>
      </div>

      <div className="flex gap-4">  
        <button
          onClick={handleEvaluationClick}
          className="px-4 py-2 bg-blue-500 text-white rounded shadow-lg hover:bg-blue-600"
        >
          Evaluate Decisions
        </button>

        <div className="flex items-center gap-3">
          <span className={`text-sm font-medium ${isOn ? "text-gray-800" : "text-gray-400"}`}>
            Feedback
          </span>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only"
              checked={isOn}
              onChange={() => setIsOn(!isOn)}
            />
            <div
              className={`w-14 h-7 bg-gray-300 rounded-full p-1 transition duration-300 ${
                isOn ? "bg-green-500" : ""
              }`}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transform transition ${
                  isOn ? "translate-x-7" : "translate-x-0"
                }`}
              ></div>
            </div>
          </label>
        </div>

      </div>

      {loading && (  // Loading spinner
        <div className="flex justify-center items-center mt-4">
          <BarLoader color="#3b82f6" size={15} />
          <p className="ml-4">Loading Evaluation...</p>
        </div>
      )}
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-white p-6 rounded-lg shadow-lg max-w-sm text-center"
              initial={{ rotateZ: -360, opacity: 0 }}
              animate={{ rotateZ: 0, opacity: 1 }}
              exit={{ rotateZ: -360, opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-xl font-semibold mb-2">Evaluation Results</h2>
              <p className="mb-4">The AI system classified {evalResAI.correct}/{evalResAI.total} ({evalResAI.acc}%) correctly.</p>
              <p className="mb-4">The human player classified {evalResPlayer.correct}/{evalResPlayer.total} ({evalResPlayer.acc}%) correctly.</p>
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 bg-red-500 text-white rounded shadow-lg hover:bg-red-600"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <div className="flex justify-center">  
        {loadingNextItem || errorFetchingNextItem ? (
          <p>Loading...</p>
        ) : (
          nextItem.image_base64 && (
            <img
              key={nextItem.key}
              src={nextItem.image_base64}
              alt="Draggable"
              className="rounded mt-4 cursor-grab bg-white p-4 transition-all duration-300 opacity-100"
              draggable="true"
              onDragStart={(e) => handleDragStart(e)}
              onLoad={() => {
                console.log("Next item loaded:", nextItem.n_seen);
                setLoadingNextItem(false);
              }}
              onError={() => {
                console.error("Failed to load next item:", nextItem.n_seen);
                setErrorFetchingNextItem(true);
                setLoadingNextItem(false);
              }}
            />
          )
        )}
      </div>

      <div className="flex w-full max-w-4xl gap-4 justify-center py-4">
        <div
          className="flex flex-col items-center w-[200px] min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "left")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">
            {examples.length > 0 ? `${examples[0].label} Images` : "Loading..."}
          </h2>
          {leftItems.map((item, index) => (
            <div key={index} className="relative flex justify-center items-center mb-2">
              <img
                src={item.image_base64}
                alt="Dropped"
                className="w-[132px] h-[132px] rounded shadow-lg bg-green-500 p-1"
              />
              {isAnimatingLeft && lastDroppedIndex === index && (
                <span className="absolute inset-0 w-[132px] h-[132px] rounded-full bg-blue-400 opacity-75 animate-ping"></span>
              )}
            </div>
          ))}
        </div>
        <div
          className="flex flex-col items-center w-[200px] min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "right")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">
            {examples.length > 0 ? `${examples[1].label} Images` : "Loading..."}
          </h2>
          {rightItems.map((item, index) => (
            <div key={index} className="relative flex justify-center items-center mb-2">
              <img
                src={item.image_base64}
                alt="Dropped"
                className="w-[132px] h-[132px] rounded shadow-lg bg-green-500 p-1"
              />
              {isAnimatingRight && lastDroppedIndex === index && (
                <span className="absolute inset-0 w-[132px] h-[132px] rounded-full bg-blue-400 opacity-75 animate-ping"></span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
