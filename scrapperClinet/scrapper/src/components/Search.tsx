import { CircularProgress } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

interface InputBarProps {
  value: string;
  handleChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleData: () => void;
  loading: boolean;
  handleCancelRequest: () => void;
}

const Search = ({
  value,
  handleChange,
  handleData,
  loading,
  handleCancelRequest,
}: InputBarProps) => {
  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      handleData();
    }
  };

  return (
    <form className="max-w-md mx-auto border-red-500 border focus:outline-none focus:border-none">
      <div className="relative w-full">
        <input
          value={value}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
          type="search"
          id="location-search"
          className="block p-2.5 w-full z-20 text-sm text-gray-900 bg-gray-50 rounded-e-lg dark:placeholder-gray-400"
          placeholder="Search for city or address"
        />
        <button
          type="button"
          className="absolute top-0 end-0 h-full p-2.5"
          onClick={loading ? handleCancelRequest : handleData}
        >
          {loading ? (
            <CircularProgress size={18} className="cursor-pointer" />
          ) : (
            <SearchIcon color="info" className="cursor-pointer" />
          )}
        </button>
      </div>
    </form>
  );
};

export default Search;
