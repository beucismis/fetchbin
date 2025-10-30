document.addEventListener("DOMContentLoaded", () => {
  const date_elements = document.querySelectorAll("[data-date]");
  date_elements.forEach((el) => {
    el.textContent = humanize_date(el.dataset.date);
  });

  init_rotating_tool_names();
  update_current_year();

  const cards = document.querySelectorAll(".output-card");
  cards.forEach((card) => {
    const public_id = card.dataset.publicId;
    if (public_id) {
      const upvote_btn = card.querySelector(".upvote-btn");
      const downvote_btn = card.querySelector(".downvote-btn");
      const score_el = card.querySelector(".score");

      upvote_btn.addEventListener("click", async () => {
        await handle_vote("upvote", public_id, score_el, upvote_btn, downvote_btn, null);
      });

      downvote_btn.addEventListener("click", async () => {
        await handle_vote("downvote", public_id, score_el, upvote_btn, downvote_btn, null);
      });
    }
  });

  const vote_widget = document.getElementById("vote-widget");
  if (vote_widget) {
    const public_id = vote_widget.dataset.publicId;
    const upvote_btn = document.getElementById("upvote-btn");
    const downvote_btn = document.getElementById("downvote-btn");
    const score_el = document.getElementById("score");

    upvote_btn.addEventListener("click", async () => {
      await handle_vote("upvote", public_id, score_el, upvote_btn, downvote_btn, null);
    });

    downvote_btn.addEventListener("click", async () => {
      await handle_vote("downvote", public_id, score_el, upvote_btn, downvote_btn, null);
    });
  }
});

function humanize_date(date_string) {
  const date = new Date(date_string);
  const now = new Date();
  const seconds = Math.round((now - date) / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);

  if (seconds < 10) {
    return "just now";
  } else if (minutes < 1) {
    return `${seconds} seconds ago`;
  } else if (minutes < 60) {
    return `${minutes} minutes ago`;
  } else if (hours < 24) {
    return `${hours} hours ago`;
  } else if (days < 7) {
    return `${days} days ago`;
  } else {
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }
}

async function handle_vote(vote_type, public_id, score_el, upvote_btn, downvote_btn, vote_message_el) {
  upvote_btn.disabled = true;
  downvote_btn.disabled = true;

  try {
    const response = await fetch(`/api/output/${public_id}/${vote_type}`, {
      method: "POST",
    });

    if (response.ok) {
      try {
        const data = await response.json();
        score_el.textContent = data.upvotes - data.downvotes;
        set_vote_state(upvote_btn, downvote_btn, vote_type);
      } catch (e) {
        console.error("Failed to parse JSON response:", e);
        upvote_btn.disabled = false;
        downvote_btn.disabled = false;
      }
    } else if (response.status === 409) {
      try {
        const error_data = await response.json();
        const message = error_data.detail || "You have already voted for this share.";
        console.log(message);
        set_vote_state(upvote_btn, downvote_btn, error_data.existing_vote || null);
      } catch (e) {
        console.error("Failed to parse error JSON:", e);
        console.log("You have already voted for this share.");
        upvote_btn.disabled = false;
        downvote_btn.disabled = false;
      }
    } else if (response.status === 429) {
      console.error("Rate limit exceeded. Please wait before voting again.");
      upvote_btn.disabled = false;
      downvote_btn.disabled = false;
    } else {
      try {
        const error_data = await response.json();
        const message = error_data.detail || "An error occurred while voting.";
        console.error(message);
      } catch (e) {
        console.error("Failed to parse error JSON. Status:", response.status);
        const response_text = await response.text();
        console.error("Response text:", response_text);
      }
      upvote_btn.disabled = false;
      downvote_btn.disabled = false;
    }
  } catch (error) {
    console.error("A network error occurred.", error);
    upvote_btn.disabled = false;
    downvote_btn.disabled = false;
  }
}

function set_vote_state(upvote_btn, downvote_btn, vote_type) {
  upvote_btn.disabled = true;
  downvote_btn.disabled = true;

  upvote_btn.classList.remove("voted");
  downvote_btn.classList.remove("voted");

  if (vote_type === "upvote") {
    upvote_btn.classList.add("voted");
  } else if (vote_type === "downvote") {
    downvote_btn.classList.add("voted");
  }
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function init_rotating_tool_names() {
  const tool_name_element = document.getElementById("tool-name");
  if (!tool_name_element) return;

  const tool_names = [
    "fastfetch",
    "neofetch",
    "curl",
    "wget",
    "htop",
    "ps",
    "df",
    "lsblk",
    "free",
    "uptime",
    "whoami",
    "uname",
    "lscpu",
    "netstat",
    "ss",
    "ping",
    "traceroute",
    "dig",
    "nslookup",
    "git status",
    "docker ps",
    "kubectl get pods",
  ];

  let current_index = 0;

  const rotate_tool_name = debounce(() => {
    tool_name_element.style.opacity = "0";

    setTimeout(() => {
      current_index = (current_index + 1) % tool_names.length;
      tool_name_element.textContent = tool_names[current_index];
      tool_name_element.style.opacity = "1";
    }, 250);
  }, 100);

  setInterval(() => {
    rotate_tool_name();
  }, 1000);
}

function update_current_year() {
  const year_element = document.getElementById("current-year");
  if (year_element) {
    year_element.textContent = new Date().getFullYear();
  }
}
