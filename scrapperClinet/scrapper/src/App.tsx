import { ChangeEvent, useEffect, useRef, useState } from "react";
import InputBar from "./components/InputBar";
import TableData from "./components/TableData";
import { Box } from "@mui/material";
import { io } from "socket.io-client";

const App = () => {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [records, setRecords] = useState<any[]>([]); // State to hold incoming records

  const abortControllerRef = useRef<AbortController | null>(null);
  let link = "https://www.indeed.com/jobs?q=node+js+developer";

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setValue(e?.target?.value);
  };

  const startScraping = async () => {
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;
    try {
      const res = await fetch("http://localhost:5000/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ indeed_page: value }),
        signal,
      });

      const data = await res?.json();
      setResponse(data);
      console.log("here");
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleData = () => {
    setLoading(true);
    startScraping();
    setValue("");
  };

  const handleCancelRequest = () => {
    if (abortControllerRef?.current) {
      abortControllerRef?.current?.abort();
    }
  };

  useEffect(() => {
    const socket = io("http://localhost:5000"); // Adjust the URL if needed

    socket.on("connect", () => {
      console.log("Connected to Socket.IO server");
    });

    socket.on("new_record", (data) => {
      console.log("New record received:", data);
      setRecords((prevRecords) => [...prevRecords, data]); // Update the records state
    });

    socket.on("disconnect", () => {
      console.log("Disconnected from Socket.IO server");
    });

    return () => {
      socket.off("connect");
      socket.off("new_record");
      socket.off("disconnect");
      socket.close();
    };
  }, []);

  return (
    <div className=" bg-black flex flex-col text-white gap-10 py-10 h-[100vh]">
      <Box className="max-w-5xl mx-auto">
        <InputBar
          value={value}
          handleChange={handleChange}
          handleData={handleData}
          loading={loading}
          handleCancelRequest={handleCancelRequest}
        />
      </Box>
      <TableData records={records} /> {/* Pass records to TableData */}
    </div>
  );
};

export default App;
